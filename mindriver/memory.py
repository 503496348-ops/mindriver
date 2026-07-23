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
    # Cross-client memory protocol (optional, backward compatible)
    clients: List[str] = field(default_factory=list)
    status: str = "active"  # active | superseded | archived
    supersedes: List[str] = field(default_factory=list)
    cognitive_type: str = ""  # preference | fact | operational | procedure | ...

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
                 category: str = "misc", entities: Optional[List[str]] = None,
                 clients: Optional[List[str]] = None, status: str = "active",
                 supersedes: Optional[List[str]] = None,
                 cognitive_type: str = "") -> str:
        path = f"{self.base_path}/{key}"
        self.mr.put(path=path, content=value,
                    metadata={"key": key, "source": source, "confidence": confidence,
                              "tags": tags or [], "user_id": self.user_id,
                              "category": category, "entities": entities or [],
                              "clients": clients or [], "status": status or "active",
                              "supersedes": supersedes or [],
                              "cognitive_type": cognitive_type or ""},
                    node_type="memory")
        self._session_buffer.append({"action": "remember", "key": key, "value": value,
                                     "category": category, "timestamp": time.time()})
        return path

    @staticmethod
    def _node_to_memory_dict(node, path: str, score: Optional[float] = None) -> Dict:
        item = {
            "key": node.metadata.get("key", ""),
            "value": node.content,
            "confidence": node.metadata.get("confidence", 0),
            "source": node.metadata.get("source", ""),
            "category": node.metadata.get("category", "misc"),
            "entities": node.metadata.get("entities", []),
            "clients": node.metadata.get("clients", []) or [],
            "status": node.metadata.get("status", "active") or "active",
            "supersedes": node.metadata.get("supersedes", []) or [],
            "cognitive_type": node.metadata.get("cognitive_type", "") or "",
            "path": path,
        }
        if score is not None:
            item["score"] = score
        return item

    def recall(self, query: str, max_results: int = 5,
               include_superseded: bool = False) -> List[Dict]:
        results = self.mr.search(query, max_results=max_results * 2 if not include_superseded else max_results)
        memories = []
        for r in results:
            node = self.mr.get(r["path"])
            if node and node.node_type == "memory":
                status = (node.metadata.get("status") or "active").lower()
                if not include_superseded and status in {"superseded", "archived", "retired"}:
                    continue
                memories.append(self._node_to_memory_dict(node, r["path"], score=r["score"]))
                # 更新访问计数
                node.access_count += 1
                if len(memories) >= max_results:
                    break
        return memories

    def get_all(self, include_superseded: bool = True) -> List[Dict]:
        memories = []
        for path, node in self.mr._index.items():
            if node.node_type == "memory" and path.startswith(self.base_path):
                status = (node.metadata.get("status") or "active").lower()
                if not include_superseded and status in {"superseded", "archived", "retired"}:
                    continue
                memories.append(self._node_to_memory_dict(node, path))
        return memories

    def update(self, key: str, value: str, confidence: float = 1.0,
               category: Optional[str] = None, status: Optional[str] = None,
               clients: Optional[List[str]] = None,
               supersedes: Optional[List[str]] = None,
               cognitive_type: Optional[str] = None) -> str:
        """更新已有记忆"""
        path = f"{self.base_path}/{key}"
        node = self.mr.get(path)
        if node:
            node.content = value
            node.updated_at = time.time()
            node.metadata["confidence"] = confidence
            if category:
                node.metadata["category"] = category
            if status is not None:
                node.metadata["status"] = status
            if clients is not None:
                node.metadata["clients"] = clients
            if supersedes is not None:
                node.metadata["supersedes"] = supersedes
            if cognitive_type is not None:
                node.metadata["cognitive_type"] = cognitive_type
            self.mr._save_index()
            self._session_buffer.append({"action": "update", "key": key, "value": value,
                                         "timestamp": time.time()})
        return path

    def supersede(self, old_key: str, new_key: str, new_value: str,
                  clients: Optional[List[str]] = None,
                  cognitive_type: str = "",
                  confidence: float = 1.0,
                  category: str = "misc") -> Dict[str, str]:
        """Write a winner memory and mark the old key as superseded."""
        new_path = self.remember(
            key=new_key,
            value=new_value,
            source="supersede",
            confidence=confidence,
            category=category,
            clients=clients,
            status="active",
            supersedes=[old_key],
            cognitive_type=cognitive_type,
        )
        old_path = self.update(old_key, self.recall_value(old_key) or "",
                               status="superseded")
        # ensure old status even if content missing
        node = self.mr.get(f"{self.base_path}/{old_key}")
        if node:
            node.metadata["status"] = "superseded"
            node.metadata["superseded_by"] = new_key
            self.mr._save_index()
        return {"old": old_path, "new": new_path}

    def recall_value(self, key: str) -> Optional[str]:
        node = self.mr.get(f"{self.base_path}/{key}")
        if node and node.node_type == "memory":
            return node.content
        return None

    def audit_protocol(self) -> Dict:
        """Audit cross-client protocol completeness and active supersession conflicts."""
        items = self.get_all(include_superseded=True)
        issues = []
        by_key = {m.get("key"): m for m in items if m.get("key")}
        for m in items:
            missing = []
            if not m.get("clients"):
                missing.append("clients")
            if not m.get("status"):
                missing.append("status")
            if "supersedes" not in m:
                missing.append("supersedes")
            if not m.get("cognitive_type"):
                missing.append("cognitive_type")
            if missing:
                issues.append({"code": "missing_protocol_fields", "key": m.get("key"), "missing": missing})
            status = (m.get("status") or "active").lower()
            for old in m.get("supersedes") or []:
                other = by_key.get(old)
                if not other:
                    issues.append({"code": "dangling_supersedes", "key": m.get("key"), "target": old})
                elif status == "active" and (other.get("status") or "active").lower() == "active":
                    issues.append({
                        "code": "active_supersedes_active",
                        "key": m.get("key"),
                        "target": old,
                    })
        return {
            "ok": not any(i["code"] == "active_supersedes_active" for i in issues),
            "total": len(items),
            "active": sum(1 for m in items if (m.get("status") or "active").lower() == "active"),
            "issues": issues,
        }

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
