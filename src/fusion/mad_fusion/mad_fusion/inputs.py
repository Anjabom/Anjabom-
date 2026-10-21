"""융합 입력(센서 팀 출력) 목록과 수신 상태 추적. ROS 의존성 없음 → 단위 테스트 용이."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

REQUIRED_KEYS = ("name", "team", "topic", "type")


@dataclass
class FusionInput:
    name: str
    team: str
    topic: str
    type: str
    timeout_sec: float = 0.5
    required: bool = True
    last_time: float | None = None
    last_msg: Any = field(default=None, repr=False)


def load_inputs(path: str) -> list[FusionInput]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    inputs = []
    names = set()
    for i, item in enumerate(data.get("inputs") or []):
        missing = [k for k in REQUIRED_KEYS if k not in item]
        if missing:
            raise ValueError(f"inputs[{i}] 에 {missing} 가 없습니다")
        if item["name"] in names:
            raise ValueError(f"입력 이름 중복: {item['name']}")
        names.add(item["name"])
        inputs.append(
            FusionInput(
                name=item["name"],
                team=item["team"],
                topic=item["topic"],
                type=item["type"],
                timeout_sec=float(item.get("timeout_sec", 0.5)),
                required=bool(item.get("required", True)),
            )
        )
    return inputs


class InputTracker:
    def __init__(self, inputs: list[FusionInput]) -> None:
        self.inputs = {i.name: i for i in inputs}

    def update(self, name: str, msg: Any, now: float) -> None:
        item = self.inputs[name]
        item.last_msg = msg
        item.last_time = now

    def stale(self, now: float) -> list[str]:
        """아직 안 들어왔거나 timeout_sec 보다 오래된 입력 이름."""
        return [i.name for i in self.inputs.values() if i.last_time is None or now - i.last_time > i.timeout_sec]

    def ready(self, now: float) -> bool:
        """required 입력이 모두 신선하면 True."""
        stale = set(self.stale(now))
        return all(not (i.required and i.name in stale) for i in self.inputs.values())

    def latest(self) -> dict[str, Any]:
        return {name: i.last_msg for name, i in self.inputs.items()}
