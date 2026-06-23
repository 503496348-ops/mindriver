---
name: mindriver
description: "Agent上下文数据库。文件系统范式管理记忆/资源/技能，分层加载(L0摘要→L1概览→L2详情)减少91% token消耗。当需要管理Agent记忆、检索上下文、分层加载知识时使用。"
  智脑星河 MindRiver — Agent上下文数据库。
  文件系统范式管理记忆/资源/技能，分层加载减少91% token消耗，让Agent越用越聪明。
triggers:
  - Agent记忆管理
  - 上下文数据库
  - 记忆分层加载
  - 文件系统范式
  - context database
  - agent memory
  - 智脑星河
  - mindriver
version: "1.0"
---

# 智脑星河 · MindRiver

> Agent上下文数据库 — 文件系统范式管理记忆/资源/技能，分层加载减少91% token消耗

## 核心能力

| 能力 | 说明 | 价值 |
|------|------|------|
| **文件系统范式** | 用`viking://`协议统一管理上下文 | 记忆/资源/技能不再分散 |
| **分层加载** | L0摘要(100token)→L1概览(2k)→L2详情 | 减少token消耗91% |
| **目录递归检索** | 先锁定目录，再精确检索 | 提高检索准确性 |
| **可视化检索轨迹** | 可观察的检索过程 | 方便调试 |
| **自动会话管理** | 会话结束自动更新记忆 | Agent越用越聪明 |

## 快速开始

### 安装

```bash
# Python包
pip install openviking

# Rust CLI（可选）
cargo install openviking-cli
```

### 配置

```bash
# 交互式配置
openviking-server init

# 检查环境
openviking-server doctor

# 启动服务
openviking-server start
```

### 使用

```bash
# 添加记忆
ov memory add "用户偏好简洁回复" --user test-user

# 查询记忆
ov memory search "用户偏好" --user test-user

# 浏览上下文
ov ls viking://user/test-user/
```

## 支持的VLM提供商

| 提供商 | 说明 |
|--------|------|
| openai | OpenAI官方API |
| kimi | Kimi代码会员 |
| glm | 智谱GLM编程计划 |

## Benchmark数据

### 用户记忆（LoCoMo基准）

| 集成对象 | 原准确率 | +MindRiver | 提升 | Token减少 |
|----------|----------|------------|------|-----------|
| Hermes | 33.38% | **82.86%** | +148% | -34% |
| Claude Code | 57.21% | **80.32%** | +40% | -63% |

### Agent经验记忆（tau2-bench）

| 场景 | 无记忆 | +MindRiver | 提升 |
|------|--------|------------|------|
| 零售 | 70.94% | **77.81%** | +6.87pp |
| 航空 | 54.38% | **66.25%** | +11.87pp |

## 文件系统范式

```
viking://
├── resources/          # 项目文档、代码库、网页
│   └── my_project/
├── user/               # 个人偏好、记忆
│   └── {user_id}/
│       ├── memories/
│       ├── resources/
│       └── skills/
└── ...
```

## 分层加载

| 层级 | Token | 用途 |
|------|-------|------|
| L0 摘要 | ~100 | 快速相关性检查 |
| L1 概览 | ~2k | 结构和关键点 |
| L2 详情 | 完整 | 按需深度读取 |

## 适用场景

- 🧠 **Agent记忆管理** — 长期记忆、用户偏好、任务经验
- 📚 **知识库检索** — 文档、代码库、网页内容
- 🤖 **多Agent协作** — 共享上下文、任务传递
- 📈 **Agent进化** — 自动学习、持续优化

## 技术栈

- Python 3.8+
- Rust CLI（可选）

## 仓库

https://github.com/503496348-ops/mindriver
