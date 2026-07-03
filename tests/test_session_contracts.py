from mindriver.session_contracts import build_hop, contract_summary


def test_session_chain_detects_drift():
    hops = [
        build_hop("ingest", {"session_id": "s1", "trace_id": "t1", "payload": {"q": 1}}),
        build_hop("retrieve", {"session_id": "s2", "trace_id": "t1", "payload": {}}),
    ]
    summary = contract_summary(hops)
    assert summary["ok"] is False
    assert "session_id drift" in summary["errors"][0]
