"""记忆管理模块 — 自动会话管理 + 结构化提取 + 去重"""
import time
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from .core import MindRiver


@dataclass
class Memory:
    key: str
    value: str
    source: str = "conversation"
    category: str = "misc"
    confidence: float = 1.0
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)

    def to_dict(self): return asdict(self)


def _make_key(text: str) -> str:
    """从文本生成短key"""
    return hashlib.md5(text.encode()).hexdigest()[:10]


class MemoryStore:
    def __init__(self, mr: MindRiver, user_id: str = "default"):
        self.mr = mr
        self.user_id = user_id
        self.base_path = f"viking://user/{user_id}/memories"
        self._session_buffer: List[Dict] = []

    def remember(self, key: str, value: str, source: str = "conversation",
                 confidence: float = 1.0, tags: Optional[List[str]] = None,
                 category: str = "misc", entities: Optional[List[str]] = None) -> str:
        path = f"{self.base_path}/{key}"
        self.mr.put(path=path, content=value,
                    metadata={"key": key, "source": source, "confidence": confidence,
                              "tags": tags or [], "user_id": self.user_id,
                              "category": category, "entities": entities or []},
                    node_type="memory")
        self._session_buffer.append({"action": "remember", "key": key, "value": value,
                                     "category": category, "timestamp": time.time()})
        return path

    def recall(self, query: str, max_results: int = 5) -> List[Dict]:
        results = self.mr.search(query, max_results=max_results)
        memories = []
        for r in results:
            node = self.mr.get(r["path"])
            if node and node.node_type == "memory":
                memories.append({
                    "key": node.metadata.get("key", ""),
                    "value": node.content,
                    "confidence": node.metadata.get("confidence", 0),
                    "source": node.metadata.get("source", ""),
                    "category": node.metadata.get("category", "misc"),
                    "entities": node.metadata.get("entities", []),
                    "path": r["path"],
                    "score": r["score"],
                })
                # 更新访问计数
                node.access_count += 1
        return memories

    def get_all(self) -> List[Dict]:
        memories = []
        for path, node in self.mr._index.items():
            if node.node_type == "memory" and path.startswith(self.base_path):
                memories.append({
                    "key": node.metadata.get("key", ""),
                    "value": node.content,
                    "confidence": node.metadata.get("confidence", 0),
                    "source": node.metadata.get("source", ""),
                    "category": node.metadata.get("category", "misc"),
                    "entities": node.metadata.get("entities", []),
                    "path": path,
                })
        return memories

    def update(self, key: str, value: str, confidence: float = 1.0,
               category: Optional[str] = None) -> str:
        """更新已有记忆"""
        path = f"{self.base_path}/{key}"
        node = self.mr.get(path)
        if node:
            node.content = value
            node.updated_at = time.time()
            node.metadata["confidence"] = confidence
            if category:
                node.metadata["category"] = category
            self.mr._save_index()
            self._session_buffer.append({"action": "update", "key": key, "value": value,
                                         "timestamp": time.time()})
        return path

    def forget(self, key: str) -> bool:
        """删除记忆"""
        path = f"{self.base_path}/{key}"
        self.mr.delete(path)
        self._session_buffer.append({"action": "forget", "key": key, "timestamp": time.time()})
        return True

    def auto_extract(self, messages: List[Dict], llm_client=None,
                     enable_dedup: bool = True) -> List[Dict]:
        """从对话自动提取并存储记忆（集成extractor+dedup）
        Args:
            messages: [{"role": "user"/"assistant", "content": "..."}, ...]
            llm_client: 可选LLM客户端
            enable_dedup: 是否启用去重
        Returns:
            存储的记忆列表
        """
        from .extractor import FactExtractor
        from .dedup import MemoryDeduplicator, MemoryAction

        # 1. 提取事实
        extractor = FactExtractor(llm_client=llm_client)
        facts = extractor.extract_from_conversation(messages)
        if not facts:
            return []

        # 2. 去重决策
        stored = []
        if enable_dedup:
            dedup = MemoryDeduplicator(llm_client=llm_client)
            existing = self.get_all()
            decisions = dedup.deduplicate(
                [f.to_dict() for f in facts],
                existing,
            )

            for fact, decision in zip(facts, decisions):
                if decision.action == MemoryAction.ADD:
                    key = _make_key(fact.text)
                    self.remember(key=key, value=fact.text,
                                  source="auto_extract", confidence=fact.confidence,
                                  category=fact.category, entities=fact.entities)
                    stored.append({"key": key, "value": fact.text, "action": "add"})
                elif decision.action == MemoryAction.UPDATE and decision.existing_key:
                    self.update(key=decision.existing_key, value=decision.new_text,
                                confidence=fact.confidence, category=fact.category)
                    stored.append({"key": decision.existing_key, "value": decision.new_text,
                                   "action": "update"})
                elif decision.action == MemoryAction.DELETE and decision.existing_key:
                    self.forget(decision.existing_key)
                    stored.append({"key": decision.existing_key, "action": "delete"})
        else:
            # 不去重，直接存储
            for fact in facts:
                key = _make_key(fact.text)
                self.remember(key=key, value=fact.text,
                              source="auto_extract", confidence=fact.confidence,
                              category=fact.category, entities=fact.entities)
                stored.append({"key": key, "value": fact.text, "action": "add"})

        return stored

    def summarize_session(self) -> str:
        if not self._session_buffer:
            return ""
        parts = []
        for i in self._session_buffer:
            if i["action"] == "remember":
                parts.append(f"记住[{i.get('category','?')}]: {i['key']} = {i['value'][:100]}")
            elif i["action"] == "update":
                parts.append(f"更新: {i['key']} = {i['value'][:100]}")
            elif i["action"] == "forget":
                parts.append(f"删除: {i['key']}")
        self._session_buffer.clear()
        return "\n".join(parts)

    def stats(self) -> Dict:
        """记忆统计"""
        all_mem = self.get_all()
        categories = {}
        for m in all_mem:
            cat = m.get("category", "misc")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total": len(all_mem),
            "by_category": categories,
            "avg_confidence": sum(m.get("confidence", 0) for m in all_mem) / max(len(all_mem), 1),
        }
