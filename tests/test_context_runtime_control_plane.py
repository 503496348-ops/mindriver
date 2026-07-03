from mindriver.context_runtime_control_plane import RuntimeSnapshot, StreamSnapshot, allowed_operator_actions, build_operator_card


def test_stream_snapshot_marks_stalled_pending_events():
    snapshot = RuntimeSnapshot(3, 0, (StreamSnapshot("task.dispatch", 10, pending=2, stale_pending=1),))
    assert snapshot.overall_health() == "attention_required"
    assert build_operator_card(snapshot)["streams"]["task.dispatch"] == "stalled"


def test_operator_actions_are_state_specific():
    assert allowed_operator_actions("blocked") == ["escalate", "resume", "retry"]
    assert "rollback" in allowed_operator_actions("verification")
