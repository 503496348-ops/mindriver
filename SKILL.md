---
name: mindriver
description: "智能体记忆运维 — 记忆存储、去重、事实提取、混合搜索"
triggers:
  - "记忆"
  - "memory"
  - "去重"
  - "dedup"
  - "事实提取"
  - "记忆搜索"
---

# MindRiver — 智能体记忆运维

为 AI Agent 提供记忆管理全链路：存储、去重、事实提取、混合检索。

## 核心能力

| 命令 | 说明 |
|------|------|
| `mindriver search <query>` | 混合搜索记忆 |
| `mindriver dedup <file>` | 记忆去重 |
| `mindriver extract --text <text>` | 从文本提取结构化事实 |
| `mindriver stats` | 存储统计 |

## 快速开始

```bash
# 搜索记忆
python3 scripts/cli.py search "deploy" --limit 5

# 提取事实
python3 scripts/cli.py extract --text "Hermes Agent 由 Nous Research 开发"

# 查看存储统计
python3 scripts/cli.py stats
```

## 架构

- `mindriver/memory.py` — MemoryStore 存储引擎
- `mindriver/dedup.py` — MemoryDeduplicator 去重决策
- `mindriver/extractor.py` — FactExtractor 事实提取
- `mindriver/core.py` — MindRiver 核心（ContextNode）
- `mindriver/hybrid_search.py` — 混合检索

## 测试

```bash
python3 -m pytest tests/ -q
```
