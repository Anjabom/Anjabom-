from mad_bringup.heartbeat import HeartbeatTracker


def test_timeout_reported_once():
    tracker = HeartbeatTracker(timeout_sec=1.0)
    tracker.update("camera", "lane_detector", 0, "", now=0.0)
    assert tracker.check_timeouts(now=0.5) == []
    assert tracker.check_timeouts(now=1.5) == ["lane_detector"]
    assert tracker.check_timeouts(now=2.0) == []


def test_revive_after_timeout():
    tracker = HeartbeatTracker(timeout_sec=1.0)
    tracker.update("gps", "gps_node", 0, "", now=0.0)
    tracker.check_timeouts(now=2.0)
    assert tracker.update("gps", "gps_node", 0, "", now=2.1) is True
    assert tracker.nodes["gps_node"].alive
