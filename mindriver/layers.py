"""分层加载模块 — L0摘要→L1概览→L2详情"""
from enum import Enum
from typing import List, Dict
from .core import MindRiver

class Layer(Enum):
    L0 = "summary"
    L1 = "overview"
    L2 = "full"

class LayeredLoader:
    def __init__(self, mr: MindRiver):
        self.mr = mr

    def scan(self, root_path: str, query: str, max_candidates: int = 20) -> List[str]:
        results = self.mr.search(query, max_results=max_candidates)
        return [r["path"] for r in results]

    def load_layer(self, paths: List[str], layer: Layer) -> Dict[str, str]:
        result = {}
        for path in paths:
            node = self.mr.get(path)
            if not node: continue
            if layer == Layer.L0: result[path] = node.summary
            elif layer == Layer.L1: result[path] = node.overview
            else: result[path] = node.content
        return result

    def progressive_load(self, root_path: str, query: str, max_final: int = 3) -> Dict[str, str]:
        candidates = self.scan(root_path, query)
        top_paths = candidates[:max_final]
        return self.load_layer(top_paths, Layer.L2)
