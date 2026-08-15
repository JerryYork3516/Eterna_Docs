# Eterna 文档变更记录 v25

内部版本：`v25`

文档性质：Eterna 文档变更与审核记录

状态：`ACTIVE`

文档更新时间：`2026-08-15 14:59`（Asia/Shanghai）

> 记录 Eterna 权威文档、知识库结构与治理规则的新增、调整和审核结果。
> 变更按日期倒序记录，并保留文档导入时的原始审核状态。

---

## 2026-08-15

### AI 情报自动化系统 Stage 1.12 A8 Fix

- 新增 `FROZEN` Personal MVP Route Amendment，以追加式治理正式消解 Stage 1.10 / 1.11 与 A8 Codex Route 的当前执行冲突
- Current Personal MVP 调度平台改为 Codex Automation；Global `08:00`、China `20:00`、Region 隔离、报告 → Git → Gmail、幂等、失败重试和安全规则继续有效
- 当前个人路线不再要求 OpenAI API `LLMProvider`、Responses API Adapter、API credential 或 Stage 1.11 原 A8–A17 强制顺序
- Stage 1.10 / 1.11 的 GitHub Actions、Python Pipeline 与 `LLMProvider` 方案作为 Future Production Route 完整保留，现有 `openai` dependency 与 lockfile 未修改
- 修正 Shared Skill、README、Global Task 与 China Task 的 Amendment 链接、读取顺序和权威优先级；未覆盖事项仍以 Stage 1.1–1.11 `FROZEN` 为准
- 未修改 Stage 1.1–1.11 `FROZEN` 历史正文或 A1–A7，未创建 Codex Automation、Workflow、API、Secret、真实日报或 Gmail 投递，未开始 Stage 1.12 A9
- `AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`，同步更新根索引与研究与探索分类索引

---

### AI 情报自动化系统 Stage 1.12 A8

- 新增 Codex AI Intelligence 运行规范入口、Shared Skill、Global Task 与 China Task，定义未来 Codex Automation 的可复用、可审核任务合同
- 将当前个人 MVP 的 A8 研究分析入口调整为 Codex Task / Skill 规范，不实现 OpenAI API `LLMProvider`；A1–A7 确定性治理与审计基础保持不变
- 继承 Source Registry、Global / China 隔离、四类 Information Status、Exact / Near / Same Event、显式事件实例锚点、完整 Evidence 追溯和 Eterna 价值提取边界
- 冻结 Prompt Injection 防线、合法来源规则、Codex 使用预算、Stage 1.8 报告结构与未来 Git / Gmail 副作用顺序
- 仅记录 Global `08:00`、China `20:00`（Asia/Shanghai）及 `Luna High` 计划配置；未创建 Codex Automation、Workflow、API 调用、Secret、真实网络采集、真实日报或 Gmail 投递
- 未修改 Stage 1.1–1.11、A1–A7 或任何 Eterna `FROZEN` 正文；`AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`，未开始 Stage 1.12 A9
- 同步更新根索引与研究与探索分类索引

---

## 2026-08-14

### AI 情报自动化系统 Stage 1.12 A5

- 实现统一公开 HTTP Transport，固定 User-Agent、四类 timeout、响应体、重定向、请求次数、Content-Type、HTTP 状态与 Rate Limit 安全边界
- 实现不可变 Raw Collector Record 与来源/条目级失败分类，不生成 CandidateItem 或分析字段
- 实现 Native RSS / Atom、GitHub 官方公开 REST API、Hugging Face 官方公开 API 与有限静态 Public Web Adapter
- 实现 Config + Source Registry 重新校验、enabled 和 Region 门禁，未知 Adapter 默认拒绝
- 新增完全合成、无 Secret、无真实网络的 Transport 与 Collector 测试；Python 3.13 Offline 测试共 256 项通过
- 未新增依赖，未修改 `pyproject.toml` / `requirements.lock`，未实现 Normalizer、Dedup、Analysis、LLM、Report、Gmail、Git Adapter 或 Workflow
- Stage 1.1–1.11 与所有 Eterna `FROZEN` 正文均未修改；`AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`，未开始 Stage 1.12 A6

### AI 情报自动化系统 Stage 1.12 A4 Fix

- 将 Git 失败状态拆分为 `Commit failed` 与 `Push failed`，使 commit 成功后的 push 失败保留原 commit SHA
- 限定 `Push failed` 只能使用原 SHA 重试至 `Pushed`，并禁止回退、重新 commit 或改写 SHA
- 补充 commit 失败恢复、push 失败恢复、SHA 完整性与终态门禁的 Offline 测试
- 未修改任何 `FROZEN` 文档，未开始 Stage 1.12 A5

## 2026-08-13

### AI 情报自动化系统 Stage 1.12 A4

- 新增 Global / China 严格分片的非敏感 Region State，并创建确定性空初始状态文件
- 实现调用方提供的 Candidate、Evidence、Event 稳定 ID 连续性，以及 first_seen / last_seen 和追加式 status_history 门禁
- 实现正整数 Revision、Report / Delivery 确定性幂等键、SHA-256 内容冲突保护及 Delivery Status 状态机
- 实现严格 State dict / JSON 序列化、深度不可变、Region 隔离、正式路径白名单与损坏状态 fail-closed
- 实现同目录临时文件、flush / fsync / `os.replace` 原子写入，以及 canonical digest 乐观并发 stale-write 防护
- Python 3.13 Offline 测试共 210 项通过；未新增依赖，未修改 `pyproject.toml` 或 `requirements.lock`
- 未实现语义 ID 生成、Collector、Normalizer、去重、聚类、分析、报告渲染、Gmail、Git Adapter 或 Workflow，未开始 Stage 1.12 A5
- Stage 1.1–1.11 与所有 Eterna `FROZEN` 正文均未修改；`AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`

## 2026-08-12

### AI 情报自动化系统 Stage 1.12 A3

- 实现 CandidateItem、Evidence、IntelligenceEvent 与 IntelligenceReport 四层不可变强类型模型
- 严格实现 Stage 1.4 冻结的 Region、来源、采集、证据关系、信息状态、可信度、重要度、技术分类和 Eterna 标签值
- 实现 timezone-aware 时间门禁、顺序引用、最小追加式状态历史及未冻结嵌套内容的受限不可变 JSON 表示
- 新增严格、确定性的 dict / JSON 序列化与反序列化，拒绝未知字段、缺失字段、错误类型、枚举拼写、naive datetime、重复 JSON 字段与非有限数值
- Python 3.13 Offline 测试共 154 项通过；compileall 与 `git diff --check` 通过，未新增第三方依赖
- 未实现 State、幂等、Revision 持久化、Collector、去重、聚类、分析、报告渲染、Gmail、Git Adapter 或 Workflow，未开始 Stage 1.12 A4
- Stage 1.1–1.11 与所有 Eterna `FROZEN` 正文均未修改；`AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`

### AI 情报自动化系统 Stage 1.12 A2

- 从 FROZEN Source Registry 精确派生 Global / China 各 3 条非空 MVP 机器配置，全部使用已登记官方名称与公开 URL
- 新增标准库 Config Loader 与只读 Registry 表格解析，严格校验 schema、Region、Collector 白名单、URL、未知字段和 Registry 引用
- 递归拒绝 Secret、Token、Cookie、Session、认证与收件人等敏感配置字段，保持默认无 Secret、无网络访问
- 新增 Region-specific 默认拒绝路径策略，只允许规范日报路径及对应 `automation/state/{region}.json`，并拒绝跨区、绝对路径、traversal 与 symlink 逃逸
- Python 3.13.15 Offline 测试共 49 项通过；未增加第三方依赖，未创建日报、正式状态、Workflow 或任何外部 API / Gmail / LLM 调用
- Source Registry、Stage 1.1–1.11 与所有 Eterna `FROZEN` 正文均未修改，未开始 Stage 1.12 A3
- `AUTOMATION_MAIN_WRITE_GATE` 保持 `NOT READY`

### AI 情报自动化系统 Stage 1.12 A1

- 完成 Python、OpenAI Responses API、Gmail API / OAuth 与 Git / `main` 四项实施前门禁核验
- 冻结并验证 Python 3.13.15，以及 Stage 1.11 批准依赖的精确补丁版本、许可证与 Python 3.13 兼容性
- 新增最小 Python 项目骨架、带传递依赖和哈希校验的 `requirements.lock`，并建立默认断网、无需 Secret 的离线测试
- 锁文件由临时固定版本 `uv 0.12.3` 生成；`uv` 仅为锁定工具，不是运行时依赖
- 当前 `main` 未启用 branch protection 或 ruleset：`AUTOMATION_MAIN_WRITE_GATE = NOT READY`
- 未来创建具有 `contents: write` 的 GitHub Actions 前必须重新审核 branch protection / ruleset，否则不得启用自动写 `main`
- 未创建 Collector、Pipeline、LLM、Gmail、Git 自动提交、GitHub Actions、真实配置、状态数据或日报实现，未开始 Stage 1.12 A2
- 未修改 Stage 1.1–1.11 或任何 Eterna `FROZEN` 正文

### AI 情报自动化系统 Stage 1.11

- 新增 Implementation Plan and Dependency Freeze v0.1，冻结 Python 3.13 单语言实现、自动化目录与最小依赖边界
- 划分 MVP、条件接入及 Later / Discovery Collector，MVP 不依赖 Search、RSSHub、浏览器自动化或封闭平台完整覆盖
- 冻结 OpenAI 官方 API、Google Gmail API、机器配置、Secret、最小权限和合法接口边界
- 采用 Region 分片非敏感 JSON 与短期 Actions 投递回执的轻量状态方案，并记录 `main` 直接写入风险与 MVP 门禁
- 定义 Unit、Fixture / Offline、Integration、End-to-End 测试体系、Fixture 范围及 Stage 1.12 确定实现顺序
- 未创建代码、Workflow、Secret、依赖文件、外部 API 调用或真实日报，未开始 Stage 1.12
- 未修改 Stage 1.1–1.10 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.10

- 新增 Automation Scheduling and Git Spec v0.1，冻结 GitHub Actions 调度平台与 `Asia/Shanghai` 业务时区
- 冻结 Global 每日 08:00、China 每日 20:00，以及两条独立任务和单次 Pipeline 顺序
- 定义仅写 `reports/**`、确定性 commit、`main` push、并发与幂等边界
- 区分采集、分析、报告、Git 和邮件失败，并冻结针对失败步骤的安全重试规则
- 明确 Secrets、最小权限、日志安全、成本和人工触发边界，禁止使用 ChatGPT / Codex 个人凭证作为运行时后端
- 未创建 Workflow、Secret、代码、Gmail/API 配置或真实日报，未开始 Stage 1.11
- 未修改 Stage 1.1–1.9 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

## 2026-08-11

### AI 情报自动化系统 Stage 1.9

- 新增 Gmail Delivery Spec v0.1，冻结 Global / China 确定性邮件主题、固定元数据与摘要结构
- 明确 Docs 日报为长期研究归档，Email 只构成摘要通知投影且不得成为新事实源
- 定义 Generated、Partial、No valid report、Failed、Revision、投递状态、失败边界与幂等语义
- 冻结 ChatGPT Gmail 可检索结构、Global / China 隔离、收件人与邮件内容安全边界
- 未写入真实邮箱地址或任何凭证，未连接 Gmail，未实现 OAuth、SMTP、Gmail API、代码、Secret 或自动化
- 未修改 Stage 1.1–1.8 或任何 Eterna `FROZEN` 上位文档，未开始 Stage 1.10
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.8

- 新增 Daily Report and Storage Spec v0.1，冻结 Global / China 日报格式、Docs 目标路径与唯一文件命名
- 定义报告时间、头部状态、固定章节、事件来源展示、P0–P3 覆盖情况与 Eterna 价值提取区块
- 明确空日报、重跑、Revision History、归档和 Global / China 隔离规则
- 只冻结目标目录结构，未创建真实日报、未来月份目录、`README.md` 或其他占位文件
- 未实现生成器、Prompt、模型、Schema、数据库、邮件、GitHub Actions、cron 或自动提交，未开始 Stage 1.9
- 未修改 Stage 1.1–1.7 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.7

- 新增 Eterna Value Extraction Rules v0.1，冻结 Eterna 影响域、三级价值边界与 Current-stage fit 原则
- 定义技术机会、竞争情报、风险信号、事实与推断分离及 Global / China 独立价值区块
- 以四份实际存在的冻结 `.md` 权威输入为依据，并显式保留 Aftelle、ECCS、Runtime 详细正式依据缺口
- 明确长期价值不等于当前施工优先级，日报不得自动修改路线、Stage、任务或 `FROZEN` 文档
- 未实现 LLM Prompt、模型调用、数值评分、算法、代码、自动决策或真实日报，未开始 Stage 1.8
- 未修改 Stage 1.1–1.6 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.6

- 新增 Analysis and Curation Rules v0.1，冻结日报准入、既有 Event 再次准入与低价值过滤规则
- 定义 Confidence、Information Status、Importance 的判断边界及日报排序原则
- 冻结 What happened、Evidence / Sources 与 Why it matters 的事实约束摘要和来源展示语义
- 保持 Global / China 独立，并仅为 Stage 1.7 预留既有分析字段的读取边界
- 未实现 LLM Prompt、模型调用、评分算法、代码、Schema、数据库或真实日报，未开始 Stage 1.7
- 未修改 Stage 1.1–1.5 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.5

- 新增 Dedup and Clustering Rules v0.1，冻结 Exact Duplicate、Near Duplicate 与 Same Event, Different Evidence 三层语义
- 定义去重判断信号、Evidence 形成、Event 聚类、冲突证据、event_id 保持与新建边界
- 明确信息状态追加式演进、Global / China 隔离、Eterna 相关性排除与 Conservative Principle
- 保持 IntelligenceEvent 到原始 URL 的完整追溯，Exact Duplicate 折叠后仍保留重复观察能力
- 未实现算法、代码、Schema、Prompt、数据库、embedding、向量检索或模型，未开始 Stage 1.6
- 未修改 Stage 1.1–1.4 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

### AI 情报自动化系统 Stage 1.4

- 新增 Intelligence Data Model v0.1，定义 CandidateItem、Evidence、IntelligenceEvent 与 IntelligenceReport 四层对象
- 冻结来源、时间、状态、技术分类、Eterna 标签与端到端可追溯字段语义
- 明确事件状态随证据追加更新但不得覆盖历史来源，并保持 Global / China 两条日报链独立
- 未实现代码、Schema、数据库、Collector、去重、聚类、Prompt、摘要、邮件或自动化，未开始 Stage 1.5
- 未修改 Stage 1.1–1.3 或任何 Eterna `FROZEN` 上位文档
- 同步更新根索引与研究与探索分类索引

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
