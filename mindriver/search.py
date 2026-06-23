"""搜索引擎 — 关键词搜索、路径匹配、标签过滤"""
from typing import List, Optional
from dataclasses import dataclass
from .core import MindRiver

@dataclass
class SearchResult:
    path: str; score: float; summary: str; node_type: str; token_count: int; match_type: str

class SearchEngine:
    def __init__(self, mr: MindRiver): self.mr = mr

    def search(self, query: str, max_results: int = 10, node_type: Optional[str] = None) -> List[SearchResult]:
        query_lower = query.lower()
        results = []
        for path, node in self.mr._index.items():
            if node_type and node.node_type != node_type: continue
            score, match_type = 0.0, ""
            if query_lower in (node.content or "").lower(): score, match_type = 1.0, "content"
            if query_lower in (node.summary or "").lower(): score, match_type = score + 3.0, "summary"
            if query_lower in path.lower(): score, match_type = score + 2.0, "path"
            tags = node.metadata.get("tags", [])
            if any(query_lower in t.lower() for t in tags): score, match_type = score + 2.0, "tag"
            if score > 0:
                results.append(SearchResult(path=path, score=score, summary=(node.summary or "")[:200],
                                            node_type=node.node_type, token_count=node.token_count, match_type=match_type))
        results.sort(key=lambda x: -x.score)
        return results[:max_results]

    def search_by_type(self, node_type: str) -> List[SearchResult]:
        return [SearchResult(path=p, score=1.0, summary=(n.summary or "")[:200], node_type=n.node_type,
                             token_count=n.token_count, match_type="type")
                for p, n in self.mr._index.items() if n.node_type == node_type]
