# Eterna 文档变更记录 v9

内部版本：`v9`

文档性质：Eterna 文档变更与审核记录

状态：`ACTIVE`

文档更新时间：`2026-08-11 10:17`（Asia/Shanghai）

> 记录 Eterna 权威文档、知识库结构与治理规则的新增、调整和审核结果。
> 变更按日期倒序记录，并保留文档导入时的原始审核状态。

---

## 2026-08-11

### AI 情报自动化系统 Stage 1.3

- 新增 Collection Architecture v0.1，定义 Source Registry 到 Analysis Pipeline 的采集层级与职责
- 评估 Official API、RSS / Feed、Web Page Monitor 与 Search Discovery 四类 Collector
- 建立 Global / China 来源与 Collector 映射、合法降级顺序与成本原则
- 明确 RSSHub 只是候选而非默认依赖，社区搜索只用于趋势发现
- 未写采集代码，未部署服务，未配置 API，未创建自动化任务，未开始 Stage 1.4
- 未修改 Stage 1.1、Stage 1.2 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.2

- 新增 Source Registry v0.1，建立 Official、Person、Community 与 Media 四类来源体系
- 统一 P0–P3 优先级、来源字段、可信度与事实引用边界
- 登记国内外官方、核心人物、技术社区、媒体与行业分析初始来源
- 写入 Eterna 关联标签与公开、合法、不绕过访问控制的合规硬约束
- 未开发采集器，未接入 API，未配置 RSSHub，未实现自动化，未开始 Stage 1.3
- 未修改 Stage 1.1 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.1

- 新增 Stage 1.1 目标与边界冻结文档
- 冻结 Global / China 每日两次独立情报任务、信息范围、信息状态与 Eterna 价值提取规则
- 写入 OpenAI / Codex 合规、账号安全和数据访问硬约束
- 记录 Stage 1 总体验收方向，未设计后续节点的具体技术方案
- 未修改任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

---

## 2026-08-06

### Markdown 格式转换

- 将仓库内 6 个 `.txt` 文件转换为 `.md` 文件
- 为转换文件补齐统一的内部版本、文档性质、状态、更新时间和摘要信息
- 将明确的章节标题、子标题和分隔符转换为 Markdown 语法，不改变原正文语义
- 同步更新根目录、相关分类索引和冻结基线中的文件路径
- 保留四份冻结正文的原版本、审核属性、冻结源哈希和冻结 Commit

### 上位输入集合定版

- 重新核对四份 Studio Next 1.0 上位输入正文的版本、标题、状态、权威范围和索引
- 确认四份正文之间不存在实质冲突
- 将 `00_Eterna/上位文档冻结基线_v0.1.md` 状态明确为 `FROZEN`
- 记录冻结内容 Commit：`392e76e45b7d733ff3ba3e0f2a633b653f3fbacf`
- 缺失的十三层详细规范、核心系统职责与数据权威边界及 Aftelle 产品北极星不纳入本次冻结

### 上位文档冻结

- 冻结 Eterna 核心宪章 v0.6，保留内部批准候选属性
- 冻结 Eterna Universe v0.3，保留内部批准候选属性
- 冻结数字居民定义 v0.6，保留内部批准属性
- 冻结 Eterna Studio North Star v0.3，保留内部批准候选属性
- 创建 `00_Eterna/上位文档冻结基线_v0.1.md`
- Studio Next 节点 1 曾标记为 `PARTIALLY_FROZEN`，后经本日重新核对将当前可引用上位输入集合定版为 `FROZEN`

### 一致性修正

- 修正 Eterna Universe v0.3 第九章中误写为 v0.2 的版本自述
- 修正 Eterna Studio North Star 的版本标记和文件名：v3.0 → v0.3
- 更新根目录、Eterna、核心领域和平台产品索引

### 替换

- 使用 Eterna Studio North Star v0.3（内部批准候选版）替换 v0.2

### 索引维护

- 更新根目录文档索引
- 更新平台产品分类索引

### 说明

v0.2 不再保留在当前文档树中，历史版本可通过 Git 提交记录追溯。

---

## 2026-07-21

### 新增

- 收录 Eterna 核心宪章 v0.6（内部批准候选版）
- 收录 Eterna Universe v0.3（内部批准候选版）
- 收录数字居民定义 v0.6（内部批准版）
- 收录 Eterna Studio North Star v0.2（内部批准候选版）
- 收录《零号公民：最后备份》正文与故事大纲

### 索引与仓库维护

- 更新根目录及对应分类索引
- 排除 Obsidian 社区插件代码和本地插件启用状态

### 说明

文档收录不改变其原始审核状态；内部批准候选版仍需完成正式审核后才能成为权威定稿。

---

## 2026-07-15

### 新增

- 创建 `Eterna_docs` 私有仓库
- 创建 `INDEX.md`
- 创建 `GLOSSARY.md`
- 创建 `CHANGELOG.md`

### 结构调整

- 建立 `00_Eterna` 至 `06_研究与探索` 的一级分类索引
- 建立 `99_Agents工作空间`，并明确其为非权威草稿区
- 将代理协作规则统一为 `AGENTS.md`
- 规范 `macOS`、`visionOS`、`watchOS` 和 Studio Legacy 的目录命名
- 排除 `.DS_Store` 和设备相关的 Obsidian 视图及工作区状态
- 统一全部 Markdown 的标题、摘要、分隔线、章节层级与版本标记格式

### 说明

当前仅建立知识库分类与治理骨架，尚未导入正式文档正文。
