# MindRiver 技术架构

## 存储引擎
- VikingDB文件系统范式：节点树+元数据索引
- SQLite持久化 + FTS5全文索引

## 分层加载
- L0（摘要<500字）→ L1（概览<2K字）→ L2（详情全量）
- 减少91% token消耗

## API
- Flask RESTful接口
- 搜索/创建/相关性预测端点
