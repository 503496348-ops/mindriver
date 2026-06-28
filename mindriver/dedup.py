"""
记忆去重器 — ADD/UPDATE/DELETE/NONE 四操作决策
灵感来源：Mem0的DEFAULT_UPDATE_MEMORY_PROMPT模式
自动检测重复记忆并合并更新
"""
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class MemoryAction(Enum):
    """记忆操作类型"""
    ADD = "add"        # 新增
    UPDATE = "update"  # 更新已有
    DELETE = "delete"  # 删除过时
    NONE = "none"      # 无变化


@dataclass
class DedupDecision:
    """去重决策"""
    action: MemoryAction
    existing_key: Optional[str] = None  # 更新/删除时指向已有记忆
    new_text: str = ""                   # 新增/更新后的内容
    reason: str = ""                     # 决策原因
    confidence: float = 0.8


# LLM去重提示
DEDUP_PROMPT = """你是一个智能记忆管理器。对比新事实和已有记忆，决定对每个新事实执行什么操作。

操作说明：
- ADD：新信息不在已有记忆中，需要新增
- UPDATE：已有记忆需要更新（信息变化、补充、修正）
- DELETE：已有记忆已被新信息取代或不再正确
- NONE：信息已存在且无需变化

规则：
1. 如果新事实与已有记忆语义相同但表述不同 → UPDATE（用更准确的表述）
2. 如果新事实是已有记忆的补充 → UPDATE（合并）
3. 如果新事实与已有记忆矛盾 → UPDATE（以新事实为准）
4. 如果新事实完全不在已有记忆中 → ADD
5. 如果已有记忆被新事实明确否定 → DELETE

返回JSON格式：
{{"decisions": [{{"action": "ADD|UPDATE|DELETE|NONE", "existing_key": "key或null", "new_text": "内容", "reason": "原因"}}]}}

已有记忆：
{existing_memories}

新事实：
{new_facts}

请做出决策："""


class MemoryDeduplicator:
    """记忆去重器 — 自动检测并合并重复记忆"""

    def __init__(self, llm_client=None, similarity_threshold: float = 0.7):
        """
        Args:
            llm_client: 可选的LLM客户端，用于语义级去重
            similarity_threshold: 文本相似度阈值（规则引擎模式）
        """
        self.llm = llm_client
        self.threshold = similarity_threshold

    def deduplicate(self, new_facts: List[Dict],
                    existing_memories: List[Dict]) -> List[DedupDecision]:
        """对新事实进行去重决策
        Args:
            new_facts: [{"text": "...", "category": "...", "confidence": 0.8}, ...]
            existing_memories: [{"key": "...", "value": "...", "path": "..."}, ...]
        Returns:
            每个新事实的决策列表
        """
        if not new_facts:
            return []

        if not existing_memories:
            # 没有已有记忆，全部ADD
            return [DedupDecision(
                action=MemoryAction.ADD,
                new_text=f.get("text", ""),
                reason="首次存储",
                confidence=f.get("confidence", 0.8),
            ) for f in new_facts]

        # 规则引擎快速去重
        rule_decisions = self._rule_dedup(new_facts, existing_memories)

        # 如果有LLM，用LLM增强
        if self.llm:
            llm_decisions = self._llm_dedup(new_facts, existing_memories)
            # 合并：LLM优先，规则补充
            return self._merge_decisions(rule_decisions, llm_decisions)

        return rule_decisions

    def _rule_dedup(self, new_facts: List[Dict],
                    existing_memories: List[Dict]) -> List[DedupDecision]:
        """规则引擎去重（快速，无LLM依赖）"""
        decisions = []

        for fact in new_facts:
            fact_text = fact.get("text", "").lower().strip()
            if not fact_text:
                continue

            best_match = None
            best_similarity = 0.0

            # 与每个已有记忆比较
            for mem in existing_memories:
                mem_value = mem.get("value", "").lower().strip()
                if not mem_value:
                    continue

                sim = self._compute_similarity(fact_text, mem_value)
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = mem

            # 决策
            if best_similarity >= self.threshold:
                # 高相似度 → 检查是否需要更新
                if self._is_contradiction(fact_text, best_match.get("value", "")):
                    decisions.append(DedupDecision(
                        action=MemoryAction.UPDATE,
                        existing_key=best_match.get("key", ""),
                        new_text=fact.get("text", ""),
                        reason=f"矛盾更新（相似度{best_similarity:.2f}）",
                        confidence=0.85,
                    ))
                elif self._is_more_detailed(fact_text, best_match.get("value", "")):
                    decisions.append(DedupDecision(
                        action=MemoryAction.UPDATE,
                        existing_key=best_match.get("key", ""),
                        new_text=fact.get("text", ""),
                        reason=f"补充更新（相似度{best_similarity:.2f}）",
                        confidence=0.8,
                    ))
                else:
                    decisions.append(DedupDecision(
                        action=MemoryAction.NONE,
                        reason=f"已存在（相似度{best_similarity:.2f}）",
                        confidence=0.9,
                    ))
            elif best_similarity >= self.threshold * 0.7:
                # 中等相似度 → 可能相关，ADD但标记
                decisions.append(DedupDecision(
                    action=MemoryAction.ADD,
                    new_text=fact.get("text", ""),
                    reason=f"相关但不同（最高相似度{best_similarity:.2f}）",
                    confidence=fact.get("confidence", 0.7),
                ))
            else:
                # 低相似度 → 新信息
                decisions.append(DedupDecision(
                    action=MemoryAction.ADD,
                    new_text=fact.get("text", ""),
                    reason="新信息",
                    confidence=fact.get("confidence", 0.8),
                ))

        return decisions

    def _llm_dedup(self, new_facts: List[Dict],
                   existing_memories: List[Dict]) -> List[DedupDecision]:
        """LLM增强去重（更精确，需要API）"""
        if not self.llm:
            return []

        try:
            # 格式化已有记忆
            mem_str = "\n".join([
                f"- key={m.get('key', '?')}: {m.get('value', '')}"
                for m in existing_memories[:20]  # 限制数量避免token爆炸
            ])
            fact_str = "\n".join([
                f"- {f.get('text', '')} (类别: {f.get('category', '?')})"
                for f in new_facts
            ])

            prompt = DEDUP_PROMPT.format(
                existing_memories=mem_str,
                new_facts=fact_str,
            )

            response = self.llm.chat(prompt, system="你是记忆管理专家。只返回JSON。")
            data = json.loads(response)

            decisions = []
            for d in data.get("decisions", []):
                action_str = d.get("action", "ADD").upper()
                try:
                    action = MemoryAction(action_str.lower())
                except ValueError:
                    action = MemoryAction.ADD

                decisions.append(DedupDecision(
                    action=action,
                    existing_key=d.get("existing_key"),
                    new_text=d.get("new_text", ""),
                    reason=d.get("reason", ""),
                    confidence=0.85,
                ))
            return decisions
        except Exception:
            return []

    def _merge_decisions(self, rule_decisions: List[DedupDecision],
                         llm_decisions: List[DedupDecision]) -> List[DedupDecision]:
        """合并规则和LLM决策，LLM优先"""
        if not llm_decisions:
            return rule_decisions
        if not rule_decisions:
            return llm_decisions

        # 按数量对齐，取LLM的结果
        merged = []
        for i, rd in enumerate(rule_decisions):
            if i < len(llm_decisions):
                ld = llm_decisions[i]
                # LLM决策置信度更高
                if ld.action != MemoryAction.NONE:
                    merged.append(ld)
                else:
                    merged.append(rd)
            else:
                merged.append(rd)

        # 如果LLM返回更多决策
        for i in range(len(rule_decisions), len(llm_decisions)):
            merged.append(llm_decisions[i])

        return merged

    @staticmethod
    def _compute_similarity(a: str, b: str) -> float:
        """混合相似度：字符级Jaccard + 关键词重叠"""
        # 字符级Jaccard
        set_a = set(a)
        set_b = set(b)
        char_sim = len(set_a & set_b) / len(set_a | set_b) if (set_a | set_b) else 0.0

        # 关键词重叠
        words_a = set(a.split())
        words_b = set(b.split())
        word_sim = len(words_a & words_b) / max(len(words_a | words_b), 1)

        # 加权平均
        return char_sim * 0.4 + word_sim * 0.6

    @staticmethod
    def _is_contradiction(new_text: str, existing: str) -> bool:
        """检测矛盾（简单规则）"""
        contradiction_pairs = [
            ("喜欢", "不喜欢"), ("是", "不是"), ("会", "不会"),
            ("能", "不能"), ("有", "没有"), ("要", "不要"),
            ("like", "dislike"), ("is", "is not"), ("can", "cannot"),
        ]
        for pos, neg in contradiction_pairs:
            if (pos in new_text and neg in existing) or (neg in new_text and pos in existing):
                return True
        return False

    @staticmethod
    def _is_more_detailed(new_text: str, existing: str) -> bool:
        """检测新文本是否更详细"""
        # 新文本明显更长且包含已有关键词
        if len(new_text) > len(existing) * 1.5:
            existing_words = set(existing.split())
            new_words = set(new_text.split())
            overlap = len(existing_words & new_words)
            return overlap >= len(existing_words) * 0.5
        return False
