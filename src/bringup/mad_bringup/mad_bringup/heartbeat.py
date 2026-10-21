"""노드 하트비트 추적 로직 (ROS 의존성 없음 → 단위 테스트 용이)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NodeState:
    team: str
    level: int
    message: str
    last_seen: float
    alive: bool = True


class HeartbeatTracker:
    def __init__(self, timeout_sec: float) -> None:
        self.timeout_sec = timeout_sec
        self.nodes: dict[str, NodeState] = {}

    def update(self, team: str, node_name: str, level: int, message: str, now: float) -> bool:
        """상태 갱신. 끊겼던 노드가 다시 살아나면 True."""
        prev = self.nodes.get(node_name)
        revived = prev is not None and not prev.alive
        self.nodes[node_name] = NodeState(team, level, message, now)
        return revived

    def check_timeouts(self, now: float) -> list[str]:
        """이번 검사에서 새로 끊긴 노드 이름 목록 (같은 노드는 한 번만 보고)."""
        lost = []
        for name, state in self.nodes.items():
            if state.alive and now - state.last_seen > self.timeout_sec:
                state.alive = False
                lost.append(name)
        return lost
