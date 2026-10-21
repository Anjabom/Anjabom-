"""센서 융합 노드 골격.

config/fusion_inputs.yaml 에 적힌 센서 팀 출력을 모두 구독하고, 필수 입력이 모두 들어오면
rate_hz 주기로 fuse() 를 호출한다. 입력 상태는 /system/status 하트비트로 보고한다.
실제 융합 로직은 fuse() 에 작성한다 (팀 리더 공동 담당).
"""

import os

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rosidl_runtime_py.utilities import get_message

from anjabom_fusion.inputs import InputTracker, load_inputs
from anjabom_interfaces.msg import NodeStatus


class FusionNode(Node):
    def __init__(self) -> None:
        super().__init__("fusion_node")
        default_inputs = os.path.join(get_package_share_directory("anjabom_fusion"), "config", "fusion_inputs.yaml")
        inputs_file = self.declare_parameter("inputs_file", default_inputs).value
        rate_hz = self.declare_parameter("rate_hz", 20.0).value

        inputs = load_inputs(inputs_file)
        self.tracker = InputTracker(inputs)
        for item in inputs:
            msg_type = get_message(item.type)
            self.create_subscription(msg_type, item.topic, self._on_input(item.name), 10)
            self.get_logger().info(f"입력 구독: {item.name} ({item.team}) {item.topic} [{item.type}]")
        if not inputs:
            self.get_logger().warn("융합 입력이 없습니다. config/fusion_inputs.yaml 에 센서 팀 출력을 추가하세요.")

        self.status_pub = self.create_publisher(NodeStatus, "/system/status", 10)
        self.create_timer(1.0 / rate_hz, self._on_timer)
        self.create_timer(1.0, self._publish_status)

    def now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def _on_input(self, name: str):
        def callback(msg) -> None:
            self.tracker.update(name, msg, self.now())

        return callback

    def _on_timer(self) -> None:
        if self.tracker.inputs and self.tracker.ready(self.now()):
            self.fuse(self.tracker.latest())

    def fuse(self, latest: dict) -> None:
        """여기에 융합/판단 로직을 작성한다. latest = {입력 이름: 마지막 메시지}.

        결과는 src/interfaces 에 정의한 메시지로 발행하고, 제어 팀이 구독한다.
        """

    def _publish_status(self) -> None:
        stale = self.tracker.stale(self.now())
        msg = NodeStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.team = "fusion"
        msg.node_name = self.get_name()
        if not self.tracker.inputs:
            msg.level, msg.message = NodeStatus.WARN, "입력 미설정"
        elif stale:
            msg.level, msg.message = NodeStatus.WARN, f"입력 없음/지연: {', '.join(stale)}"
        else:
            msg.level, msg.message = NodeStatus.OK, "모든 입력 수신 중"
        self.status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = FusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
