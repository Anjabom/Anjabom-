import pytest

from anjabom_fusion.inputs import InputTracker, load_inputs

CONFIG = """
inputs:
  - {name: lane, team: camera, topic: /lane, type: std_msgs/msg/String, timeout_sec: 0.2}
  - {name: gps, team: gps, topic: /gps/fix, type: sensor_msgs/msg/NavSatFix, timeout_sec: 0.5}
  - {name: debug, team: lidar, topic: /dbg, type: std_msgs/msg/String, required: false}
"""


def write(tmp_path, text):
    path = tmp_path / "inputs.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_load_inputs(tmp_path):
    inputs = load_inputs(write(tmp_path, CONFIG))
    assert [i.name for i in inputs] == ["lane", "gps", "debug"]
    assert inputs[2].required is False and inputs[2].timeout_sec == 0.5


def test_default_config_is_empty_list(tmp_path):
    assert load_inputs(write(tmp_path, "inputs: []\n")) == []


def test_missing_key_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_inputs(write(tmp_path, "inputs:\n  - {name: lane, team: camera, topic: /lane}\n"))


def test_ready_only_when_required_inputs_fresh(tmp_path):
    tracker = InputTracker(load_inputs(write(tmp_path, CONFIG)))
    assert not tracker.ready(now=0.0)
    tracker.update("lane", "L", now=1.0)
    assert not tracker.ready(now=1.0)  # gps 아직 없음
    tracker.update("gps", "G", now=1.0)
    assert tracker.ready(now=1.1)  # debug 는 required 아님
    assert not tracker.ready(now=1.3)  # lane 0.2초 초과
    assert set(tracker.stale(now=1.3)) == {"lane", "debug"}
    assert tracker.latest()["gps"] == "G"
