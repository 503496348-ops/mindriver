"""MindRiver 核心测试"""
import tempfile
from mindriver import MindRiver, MemoryStore, SearchEngine, LayeredLoader, Layer

def test_basic():
    with tempfile.TemporaryDirectory() as d:
        mr = MindRiver(d)
        node = mr.put("viking://user/alice/memories/偏好", "用户偏好简洁回复")
        assert node.content == "用户偏好简洁回复"
        assert node.token_count > 0
        got = mr.get("viking://user/alice/memories/偏好")
        assert got and got.content == "用户偏好简洁回复"
        mr.put("viking://user/alice/memories/习惯", "习惯早起")
        children = mr.ls("viking://user/alice/memories")
        assert len(children) == 2, f"Expected 2, got {len(children)}"
        results = mr.search("偏好")
        assert len(results) > 0
        assert mr.delete("viking://user/alice/memories/偏好")
        assert mr.get("viking://user/alice/memories/偏好") is None
        print("✅ test_basic passed")

def test_memory():
    with tempfile.TemporaryDirectory() as d:
        mr = MindRiver(d)
        store = MemoryStore(mr, user_id="test")
        store.remember("偏好", "简洁回复", tags=["style"])
        store.remember("时区", "UTC+8")
        results = store.recall("偏好")
        assert len(results) > 0
        assert len(store.get_all()) == 2
        print("✅ test_memory passed")

def test_layers():
    with tempfile.TemporaryDirectory() as d:
        mr = MindRiver(d)
        mr.put("viking://docs/long", "很长的内容。" * 100)
        loader = LayeredLoader(mr)
        candidates = loader.scan("viking://docs/", "内容")
        assert len(candidates) > 0
        l0 = loader.load_layer(candidates, Layer.L0)
        assert len(l0) > 0
        print("✅ test_layers passed")

def test_search():
    with tempfile.TemporaryDirectory() as d:
        mr = MindRiver(d)
        engine = SearchEngine(mr)
        mr.put("viking://docs/python", "Python编程指南", metadata={"tags": ["python"]})
        mr.put("viking://mem/pref", "用户偏好Python", node_type="memory")
        results = engine.search("Python")
        assert len(results) >= 2
        print("✅ test_search passed")

if __name__ == "__main__":
    test_basic()
    test_memory()
    test_layers()
    test_search()
    print("\n🎉 All tests passed!")
