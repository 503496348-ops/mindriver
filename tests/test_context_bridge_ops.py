from mindriver.context_bridge_ops import BridgeHealthProbe, BridgeOpsPanel, BridgeProcess, recommend_action


def test_ops_panel_summarizes_profiles_and_runs(tmp_path):
    rows = [BridgeProcess("default", "claude", 1, str(tmp_path), 2), BridgeProcess("codex", "codex", 2, str(tmp_path), 1)]
    assert BridgeOpsPanel().summarize(rows) == {"processes": 2, "active_runs": 3, "profiles": ["codex", "default"], "agents": ["claude", "codex"]}


def test_health_probe_recommends_block_on_missing_workspace(tmp_path):
    probe = BridgeHealthProbe(str(tmp_path))
    results = [probe.probe_workspace(str(tmp_path / "missing")), probe.probe_profile_identity()]
    assert results[0].status == "fail"
    assert recommend_action(results) == "block-run-and-repair"
