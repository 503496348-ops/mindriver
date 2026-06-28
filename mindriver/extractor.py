"""
记忆提取器 — 从对话中结构化提取事实
灵感来源：Mem0的FACT_RETRIEVAL_PROMPT模式
适配MindRiver的viking://协议存储
"""
import json
import re
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ExtractedFact:
    """提取的事实"""
    text: str
    category: str = "general"  # preference|personal|plan|professional|health|misc
    confidence: float = 0.8
    entities: List[str] = field(default_factory=list)
    source_turn: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "category": self.category,
            "confidence": self.confidence,
            "entities": self.entities,
            "source_turn": self.source_turn,
            "timestamp": self.timestamp,
        }


# 记忆提取系统提示 — 原创实现，适配中文场景
FACT_EXTRACTION_PROMPT = """你是一个个人信息组织专家，专门从对话中准确提取事实和用户偏好。

需要提取的信息类型：
1. 个人偏好：喜欢/不喜欢的食物、产品、活动、娱乐等
2. 重要个人信息：姓名、关系、重要日期
3. 计划和意图：即将到来的事件、旅行、目标
4. 专业信息：职位、工作习惯、职业目标
5. 健康信息：饮食限制、健身习惯
6. 其他：书籍、电影、品牌等杂项

规则：
- 只提取明确陈述的事实，不推断
- 每个事实独立成条
- 用JSON格式返回
- 空对话返回空列表

示例：
输入: "我叫张三，是个软件工程师"
输出: {"facts": [{"text": "姓名是张三", "category": "personal"}, {"text": "职业是软件工程师", "category": "professional"}]}

输入: "今天天气不错"
输出: {"facts": []}

输入: "我不吃辣，下周要去北京出差"
输出: {"facts": [{"text": "不吃辣", "category": "health"}, {"text": "下周要去北京出差", "category": "plan"}]}

请从以下对话中提取事实（今天是{date}）：
"""


# 记忆分类提示
CATEGORY_PROMPT = """将以下事实分类到最合适类别：
- preference（偏好）
- personal（个人信息）
- plan（计划/意图）
- professional（专业信息）
- health（健康信息）
- misc（其他）

事实：{fact}
只返回类别名称。"""


# 实体提取模式（规则引擎，不依赖LLM）
ENTITY_PATTERNS = {
    "person": [
        r"我叫(\S+)", r"我是(\S+)", r"名叫(\S+)",
        r"(\S+)是我的(?:朋友|同事|老板|家人|老师)",
    ],
    "location": [
        r"在(\S+)(?:工作|住|生活|出差|旅游)",
        r"去(\S+)(?:出差|旅游|玩)",
        r"来自(\S+)",
    ],
    "time": [
        r"(下(?:周|月|年))",
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
        r"((?:今天|明天|后天|大后天))",
    ],
    "organization": [
        r"在(\S+)(?:公司|大学|机构|团队)工作",
        r"就职于(\S+)",
    ],
}


def extract_entities(text: str) -> List[str]:
    """规则引擎提取实体（不依赖LLM，速度快）"""
    entities = []
    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and len(match) > 1 and len(match) < 20:
                    entities.append(match)
    return list(set(entities))


def classify_fact_simple(text: str) -> str:
    """简单规则分类（不依赖LLM）"""
    text_lower = text.lower()

    # 偏好关键词
    pref_keywords = ["喜欢", "不喜欢", "讨厌", "爱好", "偏好", "最爱", "最讨厌", "prefer", "like", "dislike"]
    if any(kw in text_lower for kw in pref_keywords):
        return "preference"

    # 计划关键词
    plan_keywords = ["计划", "打算", "准备", "要", "下周", "下月", "明年", "出差", "旅游", "plan"]
    if any(kw in text_lower for kw in plan_keywords):
        return "plan"

    # 健康关键词
    health_keywords = ["吃", "喝", "运动", "健身", "减肥", "健康", "过敏", "不吃", "diet", "health"]
    if any(kw in text_lower for kw in health_keywords):
        return "health"

    # 专业关键词
    prof_keywords = ["工作", "公司", "职位", "职业", "工程师", "经理", "老板", "job", "work"]
    if any(kw in text_lower for kw in prof_keywords):
        return "professional"

    # 个人信息关键词
    personal_keywords = ["叫", "名字", "生日", "家", "家人", "朋友", "name", "born"]
    if any(kw in text_lower for kw in personal_keywords):
        return "personal"

    return "misc"


class FactExtractor:
    """从事对话中提取结构化事实"""

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: 可选的LLM客户端，用于更精确的提取
                       如果不提供，使用规则引擎（速度快但精度略低）
        """
        self.llm = llm_client

    def extract_from_text(self, text: str, turn_index: int = 0) -> List[ExtractedFact]:
        """从单条文本提取事实"""
        if not text or len(text.strip()) < 3:
            return []

        # 规则引擎提取
        facts = self._extract_rules(text, turn_index)

        # 如果有LLM，用LLM增强
        if self.llm and len(text) > 10:
            llm_facts = self._extract_llm(text, turn_index)
            # 合并去重
            facts = self._merge_facts(facts, llm_facts)

        return facts

    def extract_from_conversation(self, messages: List[Dict]) -> List[ExtractedFact]:
        """从完整对话提取事实
        Args:
            messages: [{"role": "user"/"assistant", "content": "..."}, ...]
        """
        all_facts = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # 只从用户消息提取（助手消息通常是回应）
            if role == "user" and content:
                facts = self.extract_from_text(content, turn_index=i)
                all_facts.extend(facts)
        return all_facts

    def _extract_rules(self, text: str, turn_index: int) -> List[ExtractedFact]:
        """规则引擎提取（快速，无LLM依赖）"""
        facts = []

        # 1. 按句子分割
        sentences = re.split(r'[。！？\n.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 2]

        for sent in sentences:
            # 2. 提取实体
            entities = extract_entities(sent)

            # 3. 分类
            category = classify_fact_simple(sent)

            # 4. 过滤噪音（太短或太通用的句子）
            if len(sent) < 4:
                continue
            noise_patterns = ["你好", "嗯", "好的", "谢谢", "hi", "hello", "ok"]
            if sent.lower() in noise_patterns:
                continue

            # 5. 计算置信度
            confidence = 0.6  # 基础置信度
            if entities:
                confidence += 0.1  # 有实体提高
            if category != "misc":
                confidence += 0.1  # 明确分类提高
            if len(sent) > 10:
                confidence += 0.1  # 较长句子通常更有意义

            facts.append(ExtractedFact(
                text=sent,
                category=category,
                confidence=min(confidence, 1.0),
                entities=entities,
                source_turn=turn_index,
            ))

        return facts

    def _extract_llm(self, text: str, turn_index: int) -> List[ExtractedFact]:
        """LLM增强提取（更精确，需要API）"""
        if not self.llm:
            return []

        try:
            from datetime import datetime
            prompt = FACT_EXTRACTION_PROMPT.format(
                date=datetime.now().strftime("%Y-%m-%d")
            ) + f"\n{text}\n"

            response = self.llm.chat(prompt, system="你是事实提取专家。只返回JSON。")
            data = json.loads(response)
            facts = []
            for f in data.get("facts", []):
                facts.append(ExtractedFact(
                    text=f.get("text", ""),
                    category=f.get("category", "misc"),
                    confidence=0.85,
                    entities=extract_entities(f.get("text", "")),
                    source_turn=turn_index,
                ))
            return facts
        except Exception:
            return []

    def _merge_facts(self, rule_facts: List[ExtractedFact],
                     llm_facts: List[ExtractedFact]) -> List[ExtractedFact]:
        """合并规则引擎和LLM提取的结果，去重"""
        merged = list(rule_facts)
        existing_texts = {f.text.lower() for f in rule_facts}

        for lf in llm_facts:
            # 检查是否已有相似事实
            is_dup = False
            for et in existing_texts:
                if self._text_similarity(lf.text.lower(), et) > 0.7:
                    is_dup = True
                    break
            if not is_dup:
                merged.append(lf)
                existing_texts.add(lf.text.lower())

        return merged

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """简单文本相似度（字符级Jaccard）"""
        set_a = set(a)
        set_b = set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0
