"""/system/status 를 구독해 끊기거나 오류를 보고한 노드를 경고한다."""

import rclpy
from rclpy.node import Node

from mad_bringup.heartbeat import HeartbeatTracker
from mad_interfaces.msg import NodeStatus


class SystemMonitor(Node):
    def __init__(self) -> None:
        super().__init__("system_monitor")
        timeout = self.declare_parameter("timeout_sec", 2.0).value
        self.tracker = HeartbeatTracker(timeout)
        self.create_subscription(NodeStatus, "/system/status", self.on_status, 10)
        self.create_timer(0.5, self.on_timer)

    def now(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def on_status(self, msg: NodeStatus) -> None:
        if self.tracker.update(msg.team, msg.node_name, msg.level, msg.message, self.now()):
            self.get_logger().info(f"[{msg.team}] {msg.node_name} 복구됨")
        if msg.level == NodeStatus.ERROR:
            self.get_logger().error(f"[{msg.team}] {msg.node_name}: {msg.message}")
        elif msg.level == NodeStatus.WARN:
            self.get_logger().warn(f"[{msg.team}] {msg.node_name}: {msg.message}")

    def on_timer(self) -> None:
        for name in self.tracker.check_timeouts(self.now()):
            team = self.tracker.nodes[name].team
            self.get_logger().error(f"[{team}] {name} 하트비트 끊김 ({self.tracker.timeout_sec}s)")


def main() -> None:
    rclpy.init()
    node = SystemMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
