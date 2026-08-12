# AI 情报自动化系统 · Automation Scheduling and Git Spec · Stage 1.10 · v0.1

内部版本：`v0.1`

文档性质：AI 情报 GitHub Actions、调度与自动提交规范

状态：`FROZEN`

文档更新时间：`2026-08-12 09:04`（Asia/Shanghai）

> 本文件只冻结 AI 情报自动化系统未来使用 GitHub Actions 时的调度、执行、Git、失败、权限与安全边界。
> 本文件属于研究/工程规划，不构成 Workflow、代码、Secret、Gmail、外部 API 或实际自动执行实现。

---

## 1. 适用范围与继承边界

- 本规范位于 `06_研究与探索/AI_情报`，继承 Stage 1.1–1.9 已冻结的来源、数据、分析、日报、存储和邮件投递边界。
- Docs 中的 Markdown 日报是长期研究归档；Gmail 只构成对应日报的通知与摘要投影。
- Global 与 China 从来源、处理、报告、Git 提交到邮件投递始终保持独立。
- 未来自动化默认只允许写入 Stage 1.8 已冻结的 `reports/**` 路径。
- 本节点不修改 Stage 1.1–1.9 或任何 Eterna 上位 `FROZEN` 文档，不改变 Eterna 正式定义。
- 本节点只冻结规范，不创建 Workflow、代码、Secret 或实际任务，也不开始 Stage 1.11。

---

## 2. Stage 1 调度平台

Stage 1 默认调度方案冻结为 `GitHub Actions`。

选择理由：

- 与 Eterna_Docs Git 仓库直接集成；
- 不要求用户 Mac 长期在线；
- 支持计划执行、运行日志、受保护 Secret 与失败状态；
- 适合每天两次的轻量任务。

该选择只表示 Stage 1 的规划基线，不表示 Workflow 已存在、GitHub Actions 已启用或运行权限已批准。本节点不实现任何 `.github/workflows/*.yml`。

---

## 3. 业务时区与计划时间

统一业务时区：`Asia/Shanghai`。

正式计划：

| 任务 | Region | 计划时间 |
| --- | --- | --- |
| Global AI Intelligence | `Global` | 每天 `08:00 Asia/Shanghai` |
| China AI Intelligence | `China` | 每天 `20:00 Asia/Shanghai` |

时间规则：

- GitHub Actions cron 实际使用 UTC 时，后续实现必须从 `Asia/Shanghai` 正确转换，并以业务时区要求为准。
- 本节点不编写或冻结具体 cron 表达式。
- `report_date` 必须和 `Report Timezone = Asia/Shanghai` 共同确定报告业务日期。
- 计划触发时间不替代实际 `coverage_started_at`、`coverage_ended_at` 或 `report_generated_at`。
- 延迟启动或人工触发时仍记录实际时间，不把计划时间伪造为执行时间或覆盖窗口。

---

## 4. Global / China 独立任务边界

逻辑上必须存在两个独立 Job 或 Workflow 边界：

```text
Global Scheduled Run
→ Global sources
→ Global processing
→ Global report
→ Global Git commit
→ Global Gmail delivery

China Scheduled Run
→ China sources
→ China processing
→ China report
→ China Git commit
→ China Gmail delivery
```

必须保证：

- 一条链失败不自动使另一条链失败、取消或回滚。
- Global 自动化只读取 Global 来源并生成 Global Event、报告、提交和邮件。
- China 自动化只读取 China 来源并生成 China Event、报告、提交和邮件。
- 两类日报不得写入同一文件，也不得在一封正式邮件中合并。
- Global 与 China 可以因 Region 不同而并行，但各自必须遵守同 Region 的并发约束。

---

## 5. 单次执行顺序

每次 Global 或 China 运行的逻辑顺序冻结为：

```text
1. Checkout repository
2. Load frozen Stage 1 rules
3. Load Source Registry
4. Collect permitted sources
5. Normalize CandidateItem
6. Deduplicate / cluster
7. Analyze Status / Confidence / Importance
8. Generate Eterna Value Extraction
9. Generate Markdown Daily Report
10. Validate report
11. Commit report
12. Push report
13. Generate Email Summary Projection
14. Deliver Gmail
15. Record delivery result
```

顺序边界：

- 任一步只能读取前序步骤合法且通过校验的输出，不得绕过校验直接发布。
- 正常邮件投递必须发生在对应日报成功 commit 并 push 之后，确保 Email 只投影已归档 Docs 日报。
- `Record delivery result` 的存储机制与路径留待后续节点；未经单独批准不得因此扩大仓库写入范围。
- 本节点只冻结逻辑顺序，不实现、调用或测试任何步骤。

---

## 6. Git 写入范围

未来自动化默认只允许写入：

```text
06_研究与探索/AI_情报/reports/**
```

若后续确有运行状态文件需求，必须由后续节点单独批准正式路径、字段、生命周期与敏感信息边界。在此之前不得写入状态文件。

默认禁止自动修改：

- `06_研究与探索/AI_情报/Stage1/**`；
- 根 `INDEX.md`；
- `06_研究与探索/INDEX.md`；
- `CHANGELOG.md`；
- `AGENTS.md`；
- Eterna 上位 `FROZEN` 文档；
- 其他产品、工程或研究文档；
- `.github/workflows/**` 或任何配置文件。

自动日报不要求每天更新 INDEX 或 CHANGELOG。任何越界变更都必须使自动提交停止，不得自动修复、暂存或夹带该变更。

---

## 7. 自动 commit 规范

### 7.1 确定性 Commit Message

- Global：`intel: add Global AI report YYYY-MM-DD`
- China：`intel: add China AI report YYYY-MM-DD`
- Global Revision：`intel: revise Global AI report YYYY-MM-DD rN`
- China Revision：`intel: revise China AI report YYYY-MM-DD rN`

### 7.2 提交范围

- 一次 commit 只包含当前 Region、`report_date` 和 revision 对应的正式日报，以及该次运行经后续独立批准的明确产物。
- 在没有额外批准路径时，一次 commit 只能包含对应 `reports/**` 日报文件。
- 不得暂存或提交人工修改、规则文件、索引、CHANGELOG、Workflow 或其他无关文件。
- 提交前必须检查实际 diff、允许路径、报告校验结果和敏感信息。
- 无有效变化时不得制造空 commit。
- Stage 1.8 的唯一文件、修订与 Revision History 规则继续适用；重复运行不得创建第二份正式日报。

---

## 8. Push 边界

- Stage 1 当前自动化目标分支冻结为 `main`。
- 该选择是当前基线，不代表未来永久禁止改为经过批准的专用 automation branch；变更必须通过独立治理审核。
- 自动化只允许 push 当前批准目标分支。
- 禁止 force push、改写历史、删除历史日报或重写人工 commit。
- push 前必须确认本地提交只含允许路径；push 失败不得假报归档成功。
- 自动化不得创建、删除或改名其他分支，也不得自动合并未经批准的提交。

---

## 9. 并发控制

同一 `Region + report_date` 不得同时存在两个竞争写入的正式运行实例。

如果前一次运行尚未结束，后一次必须选择经后续实现冻结的安全行为之一：

- 等待前一次完成；
- 取消确认重复的运行；
- 不写入并安全退出。

任何行为都不得覆盖进行中的日报、产生竞争 commit 或重复投递。Global 与 China 因 Region 不同可以相互独立。本节点不实现或指定 GitHub concurrency key、取消策略参数或锁机制。

---

## 10. 报告与投递幂等语义

继承 Stage 1.8 / 1.9：同一 `Region + report_date + revision` 的正式日报与正式邮件投递必须具有幂等语义。

重复运行不得：

- 生成第二份正式日报或随机命名副本；
- 产生重复 IntelligenceEvent 或重复正式邮件；
- 重复提交已成功归档的相同 Revision；
- 创建没有有效变化的 commit；
- 静默覆盖已有 Revision 或历史来源。

新的正式 Revision 可以生成新的修订 commit 与明确标记的修订邮件，但必须沿用 Stage 1.8 / 1.9 的 Revision 规则。本节点不定义幂等键、状态数据库、message-id 或实现算法。

---

## 11. 失败分类

以下失败彼此独立，必须分别记录和处理：

### 11.1 Collection Failure

部分或全部允许来源未能合法取得。部分失败只有在仍能形成合规报告并如实暴露缺口时，才可进入 `Partial`；否则不得伪造覆盖或继续生成正常报告。

### 11.2 Analysis Failure

无法完成去重、聚类、Status、Confidence、Importance、摘要或 Eterna 价值分析，因而不能形成可信报告判断。

### 11.3 Report Generation Failure

无法生成或校验符合 Stage 1.8 的 Markdown 日报。报告校验失败归入此类，不得 commit 不合规日报。

### 11.4 Git Commit / Push Failure

日报已生成并通过校验，但未成功 commit 或 push，因此尚未成为已归档 Docs 日报。不得继续发送正常摘要邮件。

### 11.5 Email Delivery Failure

日报已经成功 commit 和 push，但邮件未成功投递。Docs 日报仍然有效，只允许针对邮件步骤安全重试。

采集失败、分析失败、报告失败、Git 失败和邮件失败不得合并成一个模糊状态，也不得用后一步成功掩盖前一步失败。

---

## 12. 针对性重试与失败边界

关键原则：`Collection Failure ≠ Git Commit / Push Failure ≠ Email Delivery Failure`。

重试规则：

- 重试只针对失败步骤及其必要的未完成后续步骤，不默认从头重跑完整 Pipeline。
- 日报已经成功 push、但 Gmail 投递失败时，不得重新执行采集、去重、聚类、分析或日报生成；只允许重建既有日报的 Email Summary Projection 并安全重试投递。
- commit 成功但 push 失败时，只允许先验证该 commit 与允许路径，再安全重试 push；不得重复生成日报或制造新 commit。
- 已成功归档和投递的相同 Revision 不得再次提交或发送。
- 重试不得降低事实、合规、来源、校验或安全标准。
- 不得通过提高抓取频率、绕过 Rate Limit、验证码、风控或访问控制来重试。
- 具体重试次数、退避算法、超时与告警策略留给后续实现节点。

---

## 13. Report Status 的自动化语义

继承 Stage 1.8 / 1.9：

| Report Status | Git 与邮件行为 |
| --- | --- |
| `Generated` | 通过校验后允许正常 commit、push 与邮件投递。 |
| `Partial` | 允许 commit、push 与邮件投递，但报告和邮件必须显式暴露关键来源缺口与影响。 |
| `No valid report` | 允许生成、commit、push 正式空日报并发送对应邮件；不得降低日报准入标准。 |
| `Failed` | 不得伪造或提交正常日报，不得发送正常新闻摘要。是否生成独立 Failed 状态记录及其路径由后续节点决定。 |

`Report Status`、Git 归档状态与 Stage 1.9 的 `Delivery Status` 是不同概念，必须分别记录，不得互相替代。

---

## 14. Secrets 边界

未来 GitHub Actions 所需凭证只能进入：

- GitHub Actions Secrets；
- 或其他经独立批准的受保护环境变量系统。

可能涉及的概念类别仅包括：

- LLM / API credential；
- Search / API credential；
- Gmail credential；
- 收件人配置。

本节点不创建、填写、猜测或冻结任何真实 Secret 名称和值。Secret 绝不得写入：

- Repository 文件或 Markdown；
- 日报或运行状态文件；
- 日志或错误摘要；
- Commit message；
- Email 主题或正文。

---

## 15. 最小权限原则

未来 Workflow 必须使用最小必要权限：

- 默认只需要 repository contents read；
- 只有正式写入日报与 push 的步骤才可获得有限的 contents write；
- 权限范围和有效时间必须限制到完成当前任务所需的最小值。

不得默认授予：

- repository 或 organization admin；
- Actions 管理权限；
- packages write；
- deployment 权限；
- 其他与日报生成和允许路径写入无关的权限。

实际 `permissions:` YAML、Token 类型和环境保护规则留给实现节点，本节点不创建配置。

---

## 16. 安全硬约束

未来自动化不得：

- 使用 ChatGPT / Codex 登录 Cookie；
- 自动登录 ChatGPT 网页；
- 使用 ChatGPT 个人 Session 获取模型能力；
- 将 Codex 或 ChatGPT 账号凭证作为程序 API 或运行时后端；
- 共享用户 ChatGPT、Codex、GitHub、Google 或 Gmail 账号；
- 绕过 OpenAI、Google 或第三方平台的登录、Rate Limit、验证码、风控或访问控制；
- 调用、逆向或伪造私有未授权 API。

若未来需要 LLM，必须使用明确允许的官方 API，或后续正式批准的其他合法调用方式。Codex 的职责是开发和维护系统，不得把个人 Codex / ChatGPT 会话凭证当作自动化运行依赖。

---

## 17. GitHub Actions 成本原则

- 每天只安排 Global 与 China 两次计划执行。
- 避免高频 polling，优先增量获取并控制 API 请求量。
- 控制单次运行时间、网络请求和产物规模。
- 不部署长期常驻 Runner，除非后续独立评估并批准。
- 优先使用合法免费额度和低成本方案。
- 免费额度不足时必须停止扩大消耗并报告，不得自动购买、升级或启用付费服务。

---

## 18. 日志边界

未来运行日志可以记录：

- Run ID；
- Region；
- 计划时间与实际执行时间；
- 各阶段成功或失败状态；
- 来源数量与 Event 数量；
- Report path；
- Commit SHA；
- Delivery Status；
- 非敏感错误摘要。

日志不得包含：

- Token、Cookie、Session、OAuth credential、API Key 或邮箱密码；
- Secret 值或可还原凭证的片段；
- 完整受限内容；
- 不必要的个人信息；
- ChatGPT / Codex / Gmail 登录信息。

错误日志必须最小化且可公开审查；敏感数据即使运行失败也不得输出。

---

## 19. 人工触发需求

未来应支持 `workflow_dispatch`，用于：

- 经批准的测试；
- 安全重跑；
- 正式 Revision；
- 故障恢复。

人工触发必须遵守与计划任务相同的：

- 合规和安全边界；
- Region 隔离；
- 并发与幂等规则；
- 写入路径与 Git 边界；
- Secret 与最小权限；
- 报告校验、Revision 和邮件投递规则。

人工触发不构成越过安全控制、降低准入标准或扩大写入范围的授权。本节点只冻结需求，不实现 `workflow_dispatch`。

---

## 20. 本节点明确不做

Stage 1.10 不做：

- 不创建 `.github/workflows/*.yml` 或实际 GitHub Actions 配置；
- 不实现 cron 表达式、concurrency key、permissions YAML 或 `workflow_dispatch`；
- 不创建 Secret，不配置 Gmail、SMTP、API Key 或外部 API；
- 不编写 Collector、分析、报告生成、自动 commit 或其他 Python / TypeScript / Swift 代码；
- 不编写 LLM Prompt，不调用模型；
- 不实际定时、人工触发或测试执行；
- 不生成真实日报，不实际 commit 自动日报；
- 不修改 Stage 1.1–1.9 或任何 Eterna 上位 `FROZEN` 文档；
- 不开始 Stage 1.11。

---

## 21. Stage 1.10 验收标准

Stage 1.10 只有同时满足以下条件才可 PASS：

- GitHub Actions 已冻结为 Stage 1 默认调度方案；
- `Asia/Shanghai` 业务时区、Global `08:00` 与 China `20:00` 已冻结；
- Global / China 的 Job 或 Workflow 逻辑边界独立；
- 单次 Pipeline 顺序完整；
- 自动写入范围、commit message、提交范围与 push 边界明确；
- 并发、幂等、失败分类与针对性重试规则明确；
- Generated、Partial、No valid report 与 Failed 的自动化语义明确；
- Secrets、最小权限、日志安全与低成本原则明确；
- 人工触发需求明确；
- 未使用 ChatGPT / Codex 个人凭证作为运行时后端；
- 未进入 Workflow、代码、Secret、Gmail、API 或实际自动化实现；
- 未修改任何 Eterna 上位 `FROZEN` 文档，未开始 Stage 1.11。
