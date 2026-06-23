"""
MindRiver 核心模块 — viking:// 协议上下文存储
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class ContextNode:
    """上下文节点 — 文件系统范式的最小单元"""
    path: str
    content: str = ""
    summary: str = ""
    overview: str = ""
    node_type: str = "file"  # file | dir | memory | resource | skill
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    token_count: int = 0

    @property
    def name(self) -> str:
        return self.path.rstrip("/").split("/")[-1] or "viking://"

    @property
    def parent_path(self) -> str:
        path = self.path.rstrip("/")
        after_protocol = path[9:]  # after "viking://"
        if "/" not in after_protocol:
            return "viking://"
        return path.rsplit("/", 1)[0]

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "ContextNode":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class MindRiver:
    """Agent上下文数据库主类"""

    def __init__(self, data_dir: str = "./mindriver_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, ContextNode] = {}
        self._load_index()
        # 确保根节点存在
        if "viking://" not in self._index:
            self._index["viking://"] = ContextNode(path="viking://", node_type="dir")

    def _index_path(self) -> Path:
        return self.data_dir / "index.json"

    def _load_index(self):
        idx_file = self._index_path()
        if idx_file.exists():
            try:
                data = json.loads(idx_file.read_text())
                for path, node_data in data.items():
                    self._index[path] = ContextNode.from_dict(node_data)
            except (json.JSONDecodeError, KeyError):
                self._index = {}

    def _save_index(self):
        data = {path: node.to_dict() for path, node in self._index.items()}
        self._index_path().write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _normalize_path(self, path: str) -> str:
        if not path.startswith("viking://"):
            path = "viking://" + path.lstrip("/")
        # Preserve viking:// root, strip trailing / for other paths
        if path == "viking://":
            return path
        return path.rstrip("/")

    def _estimate_tokens(self, text: str) -> int:
        cn_chars = sum(1 for c in text if ord(c) > 127)
        en_chars = len(text) - cn_chars
        return int(cn_chars / 1.5 + en_chars / 4)

    def _generate_summary(self, content: str, max_tokens: int = 100) -> str:
        if not content:
            return ""
        max_chars = max_tokens * 3
        return content if len(content) <= max_chars else content[:max_chars] + "..."

    def _generate_overview(self, content: str, max_tokens: int = 2000) -> str:
        if not content:
            return ""
        max_chars = max_tokens * 3
        return content if len(content) <= max_chars else content[:max_chars] + "..."

    def _ensure_parents(self, path: str):
        """自动创建父目录节点链"""
        # viking://user/alice/memories/偏好 -> parts=['user','alice','memories']
        after = path.replace("viking://", "").rstrip("/")
        parts = after.split("/")
        # Build parent paths: viking://user, viking://user/alice, ...
        for i in range(len(parts) - 1):
            parent = "viking://" + "/".join(parts[:i+1])
            if parent not in self._index:
                self._index[parent] = ContextNode(path=parent, node_type="dir")
        # Link each intermediate dir to its parent's children
        dir_paths = ["viking://"] + ["viking://" + "/".join(parts[:i+1]) for i in range(len(parts))]
        for i in range(1, len(dir_paths)):
            child = dir_paths[i]
            parent = dir_paths[i-1]
            if parent in self._index and child not in self._index[parent].children:
                self._index[parent].children.append(child)
        # Link the leaf node to its direct parent (not itself)
        if len(parts) > 0:
            direct_parent = "viking://" + "/".join(parts[:-1]) if len(parts) > 1 else "viking://"
            if direct_parent in self._index and path not in self._index[direct_parent].children:
                self._index[direct_parent].children.append(path)

    # ── 核心操作 ──

    def put(self, path: str, content: str, metadata: Optional[Dict] = None,
            node_type: str = "file") -> ContextNode:
        path = self._normalize_path(path)
        now = time.time()

        if path in self._index:
            node = self._index[path]
            node.content = content
            node.summary = self._generate_summary(content)
            node.overview = self._generate_overview(content)
            node.token_count = self._estimate_tokens(content)
            node.updated_at = now
            if metadata:
                node.metadata.update(metadata)
        else:
            node = ContextNode(
                path=path, content=content,
                summary=self._generate_summary(content),
                overview=self._generate_overview(content),
                token_count=self._estimate_tokens(content),
                node_type=node_type, metadata=metadata or {},
                created_at=now, updated_at=now,
            )
            self._index[path] = node
            self._ensure_parents(path)

        self._save_index()
        return node

    def get(self, path: str, layer: str = "full") -> Optional[ContextNode]:
        path = self._normalize_path(path)
        node = self._index.get(path)
        if node:
            node.access_count += 1
        return node

    def delete(self, path: str) -> bool:
        path = self._normalize_path(path)
        if path not in self._index:
            return False
        node = self._index[path]
        for child_path in list(node.children):
            self.delete(child_path)
        parent_path = node.parent_path
        if parent_path in self._index and path in self._index[parent_path].children:
            self._index[parent_path].children.remove(path)
        del self._index[path]
        self._save_index()
        return True

    def ls(self, path: str) -> List[ContextNode]:
        path = self._normalize_path(path)
        node = self._index.get(path)
        if not node:
            node = self._index.get(path + "/")
        if not node:
            return []
        return [self._index[c] for c in node.children if c in self._index]

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        query_lower = query.lower()
        results = []
        for path, node in self._index.items():
            score = 0
            if query_lower in (node.summary or "").lower(): score += 3
            if query_lower in (node.overview or "").lower(): score += 2
            if query_lower in (node.content or "").lower(): score += 1
            if query_lower in path.lower(): score += 2
            if score > 0:
                results.append({
                    "path": path, "score": score,
                    "summary": (node.summary or "")[:200],
                    "type": node.node_type, "token_count": node.token_count,
                })
        results.sort(key=lambda x: -x["score"])
        return results[:max_results]

    def tree(self, path: str = "viking://", max_depth: int = 3) -> str:
        path = self._normalize_path(path)
        lines = []
        def _walk(node_path: str, prefix: str, child_prefix: str, depth: int):
            if depth > max_depth: return
            node = self._index.get(node_path)
            if not node: return
            name = node.name
            tok = f" ({node.token_count}tok)" if node.token_count else ""
            lines.append(f"{prefix}{name}{tok}")
            valid_children = [c for c in node.children if c in self._index]
            for i, child_path in enumerate(valid_children):
                is_last = i == len(valid_children) - 1
                connector = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "
                _walk(child_path, child_prefix + connector, child_prefix + extension, depth + 1)
        _walk(path, "", "", 0)
        return "\n".join(lines) if lines else "(empty)"

    def stats(self) -> dict:
        """返回数据库统计信息"""
        total_nodes = len(self._index)
        total_tokens = sum(n.token_count for n in self._index.values())
        type_counts = {}
        for node in self._index.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        return {
            "total_nodes": total_nodes,
            "total_tokens": total_tokens,
            "type_distribution": type_counts,
            "data_dir": str(self.data_dir),
        }
