from mindriver.core import MindRiver
from mindriver.memory import Memory, MemoryStore


def test_memory_dataclass_exposes_protocol_fields():
    m = Memory(key="k", value="v", clients=["hermes"], status="active",
               supersedes=["old"], cognitive_type="preference")
    d = m.to_dict()
    assert d["clients"] == ["hermes"]
    assert d["supersedes"] == ["old"]
    assert d["cognitive_type"] == "preference"


def test_remember_recall_and_supersede_protocol(tmp_path):
    mr = MindRiver(str(tmp_path / "db"))
    store = MemoryStore(mr, user_id="u1")
    store.remember("old", "v1", clients=["hermes"], cognitive_type="fact")
    store.supersede("old", "new", "v2", clients=["hermes", "codex"], cognitive_type="fact")

    active = store.recall("v2", include_superseded=False)
    assert any(m["key"] == "new" for m in active)
    assert all(m["key"] != "old" for m in active)

    all_items = store.get_all(include_superseded=True)
    by_key = {m["key"]: m for m in all_items}
    assert by_key["old"]["status"] == "superseded"
    assert by_key["new"]["status"] == "active"
    assert "old" in by_key["new"]["supersedes"]
    assert set(by_key["new"]["clients"]) == {"hermes", "codex"}

    audit = store.audit_protocol()
    assert audit["ok"] is True
    assert audit["active"] >= 1


def test_audit_detects_active_supersedes_active(tmp_path):
    mr = MindRiver(str(tmp_path / "db"))
    store = MemoryStore(mr, user_id="u1")
    store.remember("a", "one", clients=["hermes"], status="active", cognitive_type="fact")
    store.remember("b", "two", clients=["hermes"], status="active", supersedes=["a"], cognitive_type="fact")
    audit = store.audit_protocol()
    codes = {i["code"] for i in audit["issues"]}
    assert "active_supersedes_active" in codes
    assert audit["ok"] is False
