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
  - Agent健康检查
  - 常驻团队观测
  - 运行时自检
  - provider额度监控
version: 1.5.0
---

> 📖 详细技术文档见 [references/](references/) 目录

# 智脑星河 · MindRiver

> Agent上下文数据库 — 文件系统范式管理记忆/资源/技能，分层加载减少91% token消耗


## Runtime Observability Pack（v1.3.0）

MindRiver 新增运行时观测能力，用于把“进程活着”与“智能体语义上可用”区分开：

- **PID/cmdline/heartbeat 三重校验**：避免僵尸 pid 或错进程伪装成健康。
- **语义就绪检查**：读取 pane/log/transcript，确认 agent 身份正确、已收到初始化、可接新任务。
- **事件流探测**：识别 WebSocket/subscriber 进程仍在但事件停止流动的假活状态。
- **资源与额度面板**：CPU、内存、磁盘、队列深度、provider quota 缺失时报 unknown，不报 0。
- **上下文库完整性**：检查层级分布、空库、重复事实、检索污染。

执行细则见 `references/runtime-observability-pack.md`。

## Agent Fleet Ops Panel（v1.4.0）

MindRiver 新增 `mindriver/fleet_ops.py`，把常驻团队运维状态结构化为可查询面板：

- **Agent probe**：区分 PID 活着、cmdline 匹配、heartbeat 新鲜与语义 ready/wedged/login 状态。
- **Event flow probe**：发现 subscriber/WebSocket 进程仍活着但事件流停摆的假活。
- **Login recovery plan**：为 Codex 生成 router-owned `codex login --device-auth` 计划，隔离 `CODEX_HOME`，不暴露 token/secret。
- **Context integrity**：发现空上下文、重复上下文与层级分布异常。

验证：`python3 -m pytest tests/test_fleet_ops.py -q`

## 核心能力

| 能力 | 说明 | 价值 |
|------|------|------|
| **文件系统范式** | 用`viking://`协议统一管理上下文 | 记忆/资源/技能不再分散 |
| **分层加载** | L0摘要(100token)→L1概览(2k)→L2详情 | 减少token消耗91% |
| **结构化提取** | 从对话自动提取事实+实体+分类 | 记忆不再遗漏 |
| **智能去重** | ADD/UPDATE/DELETE/NONE四操作决策 | 避免重复记忆 |
| **BM25混合搜索** | BM25+关键词+路径+标签四维评分 | 检索更精准 |
| **自动会话管理** | 会话结束自动提取→去重→存储 | Agent越用越聪明 |

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

## 新增能力（v1.2.0）— 记忆提取+去重+BM25搜索

### 自动记忆提取+去重

```python
from mindriver import MindRiver, MemoryStore

mr = MindRiver()
store = MemoryStore(mr, user_id="alice")

# 从对话自动提取+去重+存储
messages = [
    {"role": "user", "content": "我叫张三，是个软件工程师，不吃辣"},
    {"role": "assistant", "content": "好的，记住了"},
    {"role": "user", "content": "下周要去北京出差，喜欢吃粤菜"},
]
stored = store.auto_extract(messages)
# 结果：自动提取3个事实，分类，去重，存储
# [{"key": "a1b2c3d4e5", "value": "姓名是张三", "action": "add"},
#  {"key": "...", "value": "职业是软件工程师", "action": "add"},
#  {"key": "...", "value": "不吃辣", "action": "add"}]

# 查看统计
print(store.stats())
# {"total": 3, "by_category": {"personal": 1, "professional": 1, "health": 1}, "avg_confidence": 0.75}
```

### BM25混合搜索

```python
from mindriver import HybridSearchEngine

engine = HybridSearchEngine(mr._index)

# 四维评分搜索
results = engine.search("张三 工作", max_results=5)
for r in results:
    print(f"{r.path}: {r.final_score} (bm25={r.bm25_score}, kw={r.keyword_score})")
```

### 手动去重

```python
from mindriver import MemoryDeduplicator, MemoryAction

dedup = MemoryDeduplicator()
decisions = dedup.deduplicate(
    new_facts=[{"text": "张三是工程师", "category": "professional"}],
    existing_memories=[{"key": "k1", "value": "姓名是张三"}],
)
# 决策：ADD（新事实"职业"与已有"姓名"不同）
```

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


---

## 技术架构

- **存储引擎**: VikingDB文件系统范式 — 节点树+元数据索引+分层存储
- **分层加载**: L0(摘要<500字)→L1(概览<2K字)→L2(详情全量)，减少91% token消耗
- **记忆提取**: 规则引擎(实体+分类) + 可选LLM增强，从对话自动结构化提取事实
- **去重引擎**: 文本相似度(字符Jaccard+关键词重叠) + 矛盾检测 + LLM语义去重
- **搜索算法**: BM25(中英文混合分词) + 关键词精确匹配 + 路径匹配 + 标签匹配，四维加权评分
- **数据管线**: 对话→提取→去重→存储→索引→检索→上下文注入
- **API接口**: Python SDK + CLI工具 + Hermes Agent集成
- **性能**: 毫秒级检索，增量索引更新


---

## 工作流

- [ ] 1. 确认用户需求和使用场景
- [ ] 2. 加载相关代码和配置
- [ ] 3. 执行核心功能
- [ ] 4. 验证输出结果
## 2026-07-02 融合增强

- 智脑星河新增交付证据账本：记录 artifact producer/verifier 与 SHA-256，用于运行时产物可观测和可追溯。


## 2026-07-03 运行时增强

- 新增会话链路契约审计：验证 session_id/trace_id 在检索与工具执行路径中不漂移。
- 验证：新增模块通过 py_compile 和定向 pytest，代码不依赖外部服务。

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。

## 一键开箱交付

本仓库提供标准一键入口：

- `install.sh`：用户的一条命令安装与冒烟入口。
- `scripts/setup.py`：安装声明依赖并串联 doctor。
- `scripts/doctor.py`：检查 README、SKILL、入口脚本、package scripts 与产品收敛门禁。
- `scripts/smoke.py`：运行 doctor、产品收敛门禁与 Python 编译级冒烟。
- `tests/test_one_click_open_box.py`：契约测试，防止 README 写了但脚本缺失。
