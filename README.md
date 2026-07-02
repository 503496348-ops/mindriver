# 智脑星河 · MindRiver

> Agent上下文数据库 — 文件系统范式管理记忆/资源/技能，分层加载减少91% token消耗，让Agent越用越聪明。

## Runtime Observability Pack

MindRiver now includes a runtime observability pack for agent teams and context databases: PID/cmdline/heartbeat checks, semantic readiness probes, stale event-flow detection, resource/quota panels, and memory integrity audits. See `references/runtime-observability-pack.md`.

## 🧠 什么是MindRiver？

MindRiver是专为AI Agent设计的上下文数据库，用于管理Agent的记忆、资源和技能。

**核心理念：** 用文件系统范式管理Agent的"大脑"，让开发者像管理本地文件一样管理Agent的上下文。

## ✨ 核心能力

| 能力 | 说明 | 价值 |
|------|------|------|
| **文件系统范式** | 用`viking://`协议统一管理上下文 | 记忆/资源/技能不再分散 |
| **分层加载** | L0摘要(100token)→L1概览(2k)→L2详情 | 减少token消耗91% |
| **结构化提取** | 从对话自动提取事实+实体+分类 | 记忆不再遗漏 |
| **智能去重** | ADD/UPDATE/DELETE/NONE四操作决策 | 避免重复记忆 |
| **BM25混合搜索** | BM25+关键词+路径+标签四维评分 | 检索更精准 |
| **自动会话管理** | 会话结束自动提取→去重→存储 | Agent越用越聪明 |

### v1.2.0 新增：记忆提取+去重+BM25

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
# 自动提取3个事实，分类(personal/professional/health)，去重，存储

# BM25混合搜索
from mindriver import HybridSearchEngine
engine = HybridSearchEngine(mr._index)
results = engine.search("张三 工作", max_results=5)
```

## 📊 Benchmark数据

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

## 🚀 快速开始

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

### 使用示例

```bash
# 添加记忆
ov memory add "用户偏好简洁回复" --user test-user

# 查询记忆
ov memory search "用户偏好" --user test-user

# 浏览上下文
ov ls viking://user/test-user/
```

## 📁 文件系统范式

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

## 📊 分层加载

| 层级 | Token | 用途 |
|------|-------|------|
| L0 摘要 | ~100 | 快速相关性检查 |
| L1 概览 | ~2k | 结构和关键点 |
| L2 详情 | 完整 | 按需深度读取 |

## 🎯 适用场景

- 🧠 **Agent记忆管理** — 长期记忆、用户偏好、任务经验
- 📚 **知识库检索** — 文档、代码库、网页内容
- 🤖 **多Agent协作** — 共享上下文、任务传递
- 📈 **Agent进化** — 自动学习、持续优化

## 🛠️ 技术栈

- Python 3.8+
- Rust CLI（可选）

## 📄 License

AGPLv3

---

**AtomCollide-智械工坊团队出品**

---



---

## 🚀 加入AtomCollide-AI智能体实验室

**元素碰撞-AtomCollide-AI 智能体实验室** 是一个专注于AI领域的开源组织，汇聚了众多优秀学习者。

### 核心价值

**找工作：更省力，也更精准**
- 一线大厂内推通道（字节、阿里、腾讯等）
- 全链路求职赋能包（面试题库、简历优化、晋升指导）
- 线下技术沙龙 & 人脉网络

**学AI测试：真正落地，拒绝空谈**
- 从0到1实战落地体系（Skills、MCP、RAG、AI IDE等）
- 独家自研资料与工具矩阵
- 前沿技术同步与提效方案

### 知识库

- [踩坑合集](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne)
- [商业化案例库](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh)
- [科普专栏](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe)
- [Open Build](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb)
- [LLM/Agent/研究报告知识库](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd)
- [Skill封装合集](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd)
- [社区治理运营知识库](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg)

### 加入社群

| 社群 | 链接 |
|------|------|
| AI探索交流1区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI探索交流2区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI探索交流3区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI探索交流4区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI探索交流5区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI探索交流6区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI探索交流7区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI探索交流8区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI探索交流9区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI探索交流10区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI探索交流-网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI探索交流群-音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI探索交流群-微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

---

*AtomCollide-智械工坊团队出品*

---

## 组织与社群入口

**元素碰撞 · AtomCollide-AI 智能体实验室**：面向学习者、创作者与自动化实践者，持续沉淀可复用的 AI Agent 产品、工作流与工程经验。使命：**for the learner**。

> 请选择 1 个常用社群加入，内容全域同步，无需重复加入。

### 知识库

| 知识库 | 链接 |
|---|---|
| 踩坑合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne) |
| 商业化案例库 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh) |
| 科普专栏 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe) |
| Open Build | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb) |
| LLM / Agent / 研究报告 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd) |
| Skill 封装合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd) |
| 社区治理运营 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg) |

### 社群邀请

| 社群 | 链接 |
|---|---|
| AI 探索交流 1 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI 探索交流 2 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI 探索交流 3 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI 探索交流 4 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI 探索交流 5 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI 探索交流 6 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI 探索交流 7 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI 探索交流 8 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI 探索交流 9 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI 探索交流 10 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI 探索交流 — 网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI 探索交流群 — 音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI 探索交流群 — 微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

---

AtomCollide-智械工坊团队出品。更多产品见：[AtomCollide Product Matrix](https://503496348-ops.github.io/atomcollide-product-matrix/)。


## 示例输出

本仓库的最小可验证使用路径：

1. 阅读 README 的 Quick Start / 使用说明，完成本地安装或配置。
2. 按仓库提供的命令、脚本或入口运行一次最小任务。
3. 对照本产品定位验证输出：**智脑星河（MindRiver）** 属于 **Agent上下文** 产品，目标是把输入材料转化为可检查、可复用的结果。
4. 若运行环境暂不可用，先通过 README、CHANGELOG、CI 状态和源码结构完成静态验收，再补充真实截图或录屏。

> 维护要求：后续每次发布都应把真实运行截图、CLI 输出、网页截图或 API 响应样例补充到本节，避免仓库首页只描述能力、不展示结果。

## Governance Links

- [LICENSE](LICENSE)
- [CHANGELOG](CHANGELOG.md)
- [SECURITY](SECURITY.md)
- [CONTRIBUTING](CONTRIBUTING.md)


