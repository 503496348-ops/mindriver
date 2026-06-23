"""记忆管理模块 — 自动会话管理"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from .core import MindRiver

@dataclass
class Memory:
    key: str
    value: str
    source: str = "conversation"
    confidence: float = 1.0
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    def to_dict(self): return asdict(self)

class MemoryStore:
    def __init__(self, mr: MindRiver, user_id: str = "default"):
        self.mr = mr
        self.user_id = user_id
        self.base_path = f"viking://user/{user_id}/memories"
        self._session_buffer: List[Dict] = []

    def remember(self, key: str, value: str, source: str = "conversation",
                 confidence: float = 1.0, tags: Optional[List[str]] = None) -> str:
        path = f"{self.base_path}/{key}"
        self.mr.put(path=path, content=value,
                    metadata={"key": key, "source": source, "confidence": confidence,
                              "tags": tags or [], "user_id": self.user_id},
                    node_type="memory")
        self._session_buffer.append({"action": "remember", "key": key, "value": value, "timestamp": time.time()})
        return path

    def recall(self, query: str, max_results: int = 5) -> List[Dict]:
        results = self.mr.search(query, max_results=max_results)
        memories = []
        for r in results:
            node = self.mr.get(r["path"])
            if node and node.node_type == "memory":
                memories.append({"key": node.metadata.get("key", ""), "value": node.content,
                                 "confidence": node.metadata.get("confidence", 0),
                                 "source": node.metadata.get("source", ""), "path": r["path"], "score": r["score"]})
        return memories

    def get_all(self) -> List[Dict]:
        memories = []
        for path, node in self.mr._index.items():
            if node.node_type == "memory" and path.startswith(self.base_path):
                memories.append({"key": node.metadata.get("key", ""), "value": node.content,
                                 "confidence": node.metadata.get("confidence", 0),
                                 "source": node.metadata.get("source", ""), "path": path})
        return memories

    def summarize_session(self) -> str:
        if not self._session_buffer: return ""
        parts = [f"记住: {i['key']} = {i['value'][:100]}" for i in self._session_buffer if i["action"] == "remember"]
        self._session_buffer.clear()
        return "\n".join(parts)
