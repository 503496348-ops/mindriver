"""
混合搜索引擎 — BM25 + 关键词 + 路径匹配
灵感来源：Mem0的BM25_BASED_RETRIEVAL_PROMPT
在MindRiver原有搜索基础上增加BM25评分
"""
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class HybridResult:
    """混合搜索结果"""
    path: str
    content: str
    bm25_score: float = 0.0
    keyword_score: float = 0.0
    path_score: float = 0.0
    tag_score: float = 0.0
    final_score: float = 0.0
    match_type: str = ""
    node_type: str = ""


def tokenize(text: str) -> List[str]:
    """中英文混合分词（规则引擎，不依赖外部库）"""
    text = text.lower()
    # 提取中文字符（每个字作为token）
    cn_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
    # 提取英文单词
    en_words = re.findall(r'[a-z0-9_]+', text)
    return cn_chars + en_words


def compute_bm25_score(query_tokens: List[str], doc_tokens: List[str],
                       avg_dl: float, N: int, df_map: Dict[str, int],
                       k1: float = 1.5, b: float = 0.75) -> float:
    """计算BM25分数
    Args:
        query_tokens: 查询词列表
        doc_tokens: 文档词列表
        avg_dl: 平均文档长度
        N: 文档总数
        df_map: 词→文档频率映射
        k1: 词频饱和参数
        b: 文档长度归一化参数
    """
    if not doc_tokens or not query_tokens:
        return 0.0

    doc_len = len(doc_tokens)
    doc_counter = Counter(doc_tokens)
    score = 0.0

    for qt in query_tokens:
        if qt not in df_map:
            continue
        df = df_map[qt]
        tf = doc_counter.get(qt, 0)
        if tf == 0:
            continue

        # IDF部分
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
        # TF部分
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / max(avg_dl, 1)))
        score += idf * tf_norm

    return score


class HybridSearchEngine:
    """混合搜索引擎 — BM25 + 关键词 + 路径 + 标签"""

    def __init__(self, index: Dict, weights: Optional[Dict[str, float]] = None):
        """
        Args:
            index: MindRiver的_index字典 {path: ContextNode}
            weights: 各维度权重 {"bm25": 0.5, "keyword": 0.2, "path": 0.15, "tag": 0.15}
        """
        self.index = index
        self.weights = weights or {
            "bm25": 0.50,
            "keyword": 0.20,
            "path": 0.15,
            "tag": 0.15,
        }
        self._doc_tokens: Dict[str, List[str]] = {}
        self._df_map: Dict[str, int] = {}
        self._avg_dl: float = 0.0
        self._N: int = 0
        self._rebuild_index()

    def _rebuild_index(self):
        """重建BM25索引"""
        self._doc_tokens = {}
        df_counter: Dict[str, int] = {}
        total_len = 0

        for path, node in self.index.items():
            # 合并所有文本字段
            text = " ".join([
                node.content or "",
                node.summary or "",
                node.overview or "",
            ])
            tokens = tokenize(text)
            if tokens:
                self._doc_tokens[path] = tokens
                total_len += len(tokens)
                unique_tokens = set(tokens)
                for t in unique_tokens:
                    df_counter[t] = df_counter.get(t, 0) + 1

        self._N = len(self._doc_tokens)
        self._avg_dl = total_len / max(self._N, 1)
        self._df_map = df_counter

    def search(self, query: str, max_results: int = 10,
               node_type: Optional[str] = None,
               category_filter: Optional[str] = None) -> List[HybridResult]:
        """混合搜索
        Args:
            query: 搜索查询
            max_results: 最大结果数
            node_type: 过滤节点类型
            category_filter: 过滤记忆类别
        """
        if not query or not self.index:
            return []

        query_tokens = tokenize(query)
        query_lower = query.lower()
        results = []

        for path, node in self.index.items():
            # 类型过滤
            if node_type and node.node_type != node_type:
                continue
            # 类别过滤
            if category_filter:
                node_cat = node.metadata.get("category", "")
                if node_cat != category_filter:
                    continue

            doc_tokens = self._doc_tokens.get(path, [])

            # 1. BM25分数
            bm25 = compute_bm25_score(
                query_tokens, doc_tokens,
                self._avg_dl, self._N, self._df_map
            )

            # 2. 关键词精确匹配
            keyword = 0.0
            content_lower = (node.content or "").lower()
            summary_lower = (node.summary or "").lower()
            if query_lower in content_lower:
                keyword += 3.0
            if query_lower in summary_lower:
                keyword += 5.0
            # 部分匹配
            for qt in query_tokens:
                if qt in content_lower:
                    keyword += 0.5
                if qt in summary_lower:
                    keyword += 1.0

            # 3. 路径匹配
            path_score = 0.0
            if query_lower in path.lower():
                path_score = 5.0
            for qt in query_tokens:
                if qt in path.lower():
                    path_score += 1.0

            # 4. 标签匹配
            tag_score = 0.0
            tags = node.metadata.get("tags", [])
            for tag in tags:
                if query_lower in tag.lower():
                    tag_score += 3.0
                for qt in query_tokens:
                    if qt in tag.lower():
                        tag_score += 1.0

            # 加权总分
            final = (
                self.weights["bm25"] * bm25 +
                self.weights["keyword"] * keyword +
                self.weights["path"] * path_score +
                self.weights["tag"] * tag_score
            )

            if final > 0:
                # 确定匹配类型
                scores = {"bm25": bm25, "keyword": keyword, "path": path_score, "tag": tag_score}
                match_type = max(scores, key=lambda k: scores[k])

                results.append(HybridResult(
                    path=path,
                    content=(node.content or "")[:200],
                    bm25_score=round(bm25, 3),
                    keyword_score=round(keyword, 3),
                    path_score=round(path_score, 3),
                    tag_score=round(tag_score, 3),
                    final_score=round(final, 3),
                    match_type=match_type,
                    node_type=node.node_type,
                ))

        results.sort(key=lambda x: -x.final_score)
        return results[:max_results]

    def rebuild(self):
        """手动重建索引（数据变更后调用）"""
        self._rebuild_index()

    def stats(self) -> Dict:
        """索引统计"""
        return {
            "total_docs": self._N,
            "avg_doc_length": round(self._avg_dl, 1),
            "vocabulary_size": len(self._df_map),
            "weights": self.weights,
        }
