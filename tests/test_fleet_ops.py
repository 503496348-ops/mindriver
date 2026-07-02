from __future__ import annotations

from mindriver.fleet_ops import (
    AgentProbe,
    EventFlowProbe,
    FleetOpsPanel,
    LoginRecoveryRequest,
    ProbeStatus,
)


def test_fleet_ops_panel_separates_process_alive_from_semantic_ready():
    panel = FleetOpsPanel()
    panel.add_agent(AgentProbe(
        name="coder",
        pid_alive=True,
        cmdline_matches=True,
        heartbeat_age_seconds=12,
        semantic_state="wedged",
        quota_remaining=None,
    ))

    report = panel.evaluate()

    assert report["agents"]["coder"]["status"] == ProbeStatus.DEGRADED.value
    assert "semantic_wedged" in report["agents"]["coder"]["reasons"]
    assert report["agents"]["coder"]["quota_remaining"] == "unknown"


def test_event_flow_probe_detects_stale_subscriber_even_when_process_alive():
    panel = FleetOpsPanel(now=1_000)
    panel.add_event_flow(EventFlowProbe(name="feishu-events", process_alive=True, last_event_at=880, max_silence_seconds=60))

    report = panel.evaluate()

    assert report["event_flows"]["feishu-events"]["status"] == ProbeStatus.DEGRADED.value
    assert "event_flow_stale" in report["event_flows"]["feishu-events"]["reasons"]


def test_login_recovery_plan_is_zero_llm_and_token_safe():
    request = LoginRecoveryRequest(agent="coder", cli="codex", cred_home="/private/coder")
    plan = request.to_plan()

    assert plan["command"] == ["codex", "login", "--device-auth"]
    assert plan["env"] == {"CODEX_HOME": "/private/coder/.codex"}
    assert plan["handled_by"] == "router"
    assert "token" not in plan["user_visible"].lower()
    assert "secret" not in plan["user_visible"].lower()


def test_memory_integrity_flags_empty_and_duplicate_context_nodes():
    panel = FleetOpsPanel()
    panel.add_context_node("viking://user/a/memories/1", "用户喜欢简洁", tier="L1")
    panel.add_context_node("viking://user/a/memories/2", "用户喜欢简洁", tier="L1")
    panel.add_context_node("viking://user/a/memories/empty", "", tier="L2")

    report = panel.evaluate()

    assert report["context_integrity"]["status"] == ProbeStatus.DEGRADED.value
    assert "duplicate_context" in report["context_integrity"]["reasons"]
    assert "empty_context" in report["context_integrity"]["reasons"]
