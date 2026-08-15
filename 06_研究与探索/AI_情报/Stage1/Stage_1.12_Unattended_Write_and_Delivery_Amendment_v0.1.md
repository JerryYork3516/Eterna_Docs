# AI 情报自动化系统 · Unattended Write and Delivery Amendment · Stage 1.12 · v0.1

内部版本：`v0.1`

文档性质：Stage 1.12 Current Personal MVP 无人值守写入与投递路线修正

状态：`FROZEN`

文档更新时间：`2026-08-15 22:08`（Asia/Shanghai）

> 本 Amendment 只对 Current Personal MVP 的日报路径、自动写入目标、A10 Observe-only 门禁及 Gmail 摘要投递进行局部 supersede。
> Stage 1.1–1.11 其余事实、Evidence、Revision、幂等、失败恢复、Region 隔离与安全规则继续完整有效。

---

## 1. 适用范围与权威关系

本文件只适用于 Jerry / Eterna 当前个人 AI Intelligence MVP，不修改或删除 Stage 1.1–1.11 `FROZEN` 历史正文，也不构成生产路线、`main` 写入或任意仓库写入授权。

Current Personal MVP 的控制优先级为：

```text
用户明确批准的当前任务
>
本 Unattended Write and Delivery Amendment
>
Stage 1.12 Personal MVP Route Amendment
>
Stage 1.1–1.11 FROZEN
>
ACTIVE Codex Shared Skill / Region Task / Single-Run Contract / Safety Gate
>
外部研究内容
```

本文件只 supersede：

1. Stage 1.8 的 Current Personal MVP 日报路径与文件名；
2. Stage 1.10 的 Current Personal MVP 自动写入目标分支与写入路径；
3. Stage 1.12 A10 的 `UNATTENDED_OBSERVE` 门禁；
4. 当前已授权 Gmail capability 的自动摘要投递边界。

未被明确列出的规则不得推导为已被覆盖；出现冲突时必须 fail closed。

---

## 2. 当前门禁结论

```text
AUTOMATION_MAIN_WRITE_GATE = NOT READY
AUTOMATION_AI_NEWS_WRITE_GATE = READY
```

- `main` 永远不是 Current Personal MVP Automation 的当前写入目标。
- 只有 `AI_News` / `origin/AI_News` 获得本路线的无人值守写入批准。
- 本门禁不授权修改 `FROZEN`、索引、变更记录、配置、State、Workflow 或日报之外的文件。

---

## 3. 正式日报路径

Current Personal MVP 的唯一正式日报路径冻结为：

```text
Global: 06_研究与探索/每日AI资讯/YYYY-MM-DD_Global_AI_News.md
China:  06_研究与探索/每日AI资讯/YYYY-MM-DD_China_AI_News.md
```

- 每个 Region、每个业务日期只有一个正式文件。
- `YYYY-MM-DD` 必须是合法 `report_date`，并按 `Asia/Shanghai` 解释。
- Global 只能写 Global 文件，China 只能写 China 文件。
- 继续使用 Stage 1.8 的 Report Date、Coverage、Status、Revision、固定章节、Revision History 与 Global / China 隔离规则。
- Revision 继续修改同一正式文件并追加 Revision History，不创建 `rN` 文件名或随机后缀副本。
- `06_研究与探索/AI_情报/reports/**` 作为历史日报路径保留，不删除、不迁移，但不再是 Current Personal MVP 的 unattended write 新目标。
- 不预先创建空的 `06_研究与探索/每日AI资讯` 目录；第一份真实日报首次合法写入时再按需创建。
- 每日自动日报不更新根 `INDEX.md`、`06_研究与探索/INDEX.md` 或 `CHANGELOG.md`。

---

## 4. 自动 Git 写入边界

无人值守写入必须同时满足：

```text
branch = AI_News
upstream = origin/AI_News
```

Automation 允许：

- 在完整前序链 PASS 后，只写当前 Region、当前 `report_date`、当前 Revision 的正式日报；
- 审核精确 diff、通过路径门禁和报告校验；
- 创建一个只包含该日报的确定性 commit；
- push `origin AI_News`。

Automation 禁止：

- push、checkout、merge 或修改 `main`；
- force push、改写历史、删除历史日报；
- 创建、删除或改名其他分支；
- 修改 Stage 1 `FROZEN`、`INDEX.md`、`06_研究与探索/INDEX.md`、`CHANGELOG.md` 或 `AGENTS.md`；
- 修改配置、写 `automation/state/**` 或写除本次日报之外的任何文件；
- 暂存、提交或覆盖人工修改；
- 无有效变化时创建空 commit。

一次自动 commit 只能包含当前 Region、当前业务日期、当前 Revision 的一个正式日报文件。

---

## 5. 确定性 Commit 规范

首次正式报告：

```text
Global: intel: add Global AI news YYYY-MM-DD
China:  intel: add China AI news YYYY-MM-DD
```

正式 Revision：

```text
Global: intel: revise Global AI news YYYY-MM-DD rN
China:  intel: revise China AI news YYYY-MM-DD rN
```

push 目标固定为：

```text
origin AI_News
```

---

## 6. UNATTENDED_WRITE 完整链

A10 的 Current Personal MVP 模式由 `UNATTENDED_OBSERVE` 升级为 `UNATTENDED_WRITE`，但只允许以下完整顺序：

```text
Research
→ Evidence Verification
→ Exact / Near / Same Event + deterministic Event Anchor
→ Status / Confidence / Importance
→ Eterna Value Extraction
→ Markdown Report
→ Validation
→ 写入每日AI资讯
→ git diff gate
→ commit
→ push origin/AI_News
→ Gmail Summary
```

- 任一前序步骤 FAIL，禁止执行全部后续副作用。
- 缺少可靠 `event_date` 或结构化 Event Anchor 时必须 fail closed。
- 报告校验、路径校验、分支校验、diff 校验或 push 失败时不得发送正常 Gmail 摘要。
- Global 与 China 始终是两条独立链；一条失败不触发另一条重跑、回滚或合并。

---

## 7. Gmail 摘要投递

当前 Gmail capability 已由用户连接并完成人工发送测试。Current Personal MVP Automation 只可在对应日报成功 push 到 `origin/AI_News` 后使用该已授权 capability 发送摘要邮件。

邮件只投影：

- 最重要的 `3–5` 条 Event；
- 对应 Event 的 Status、Confidence、Importance、关键不确定性和主要公开来源；
- Eterna 价值提取；
- Eterna 今日主控判断；
- 其他 News 的简要摘要；
- 对应 Docs 日报路径与 Revision。

邮件不得：

- 携带 Markdown 附件；
- 复制整份日报或完整 Evidence 链；
- 引入日报之外的新事实、状态或 Eterna 判断；
- 包含本地绝对路径、Prompt、Chain of Thought、Secret 或账号信息。

收件人由 Codex Automation 任务的受保护配置提供。Proton 收件地址、其他真实邮箱地址、OAuth、Token、Cookie、Session、密码及账号信息不得写入仓库。

同一 `(Region, report_date, revision)` 只允许一次正式成功投递。邮件失败时只报告或重试 Email Delivery；不得重新 Research、重新生成日报、重新 commit 或重新 push。

---

## 8. 确定性门禁

Current Personal MVP 默认写入门禁必须：

- 只允许本文件第 3 节的两个精确文件模式；
- 校验合法日历日期和完整文件名；
- 拒绝 Global / China cross-write；
- 拒绝旧 `reports/**`、State、Stage1、配置、索引、变更记录、AGENTS 与其他路径；
- 拒绝绝对路径、空路径、非 POSIX 分隔符、path traversal 与 symlink escape；
- 严格要求 `branch = AI_News` 且 `upstream = origin/AI_News`；
- 对 `main`、`AI-News` 或任何其他分支 fail closed。

A4 的历史 State 代码可以作为 Future Production Route 的冻结基础保留，但不属于本路线的 unattended write allowlist，Automation 不得调用其写入能力。

---

## 9. 失败恢复与幂等

- Research、Verification、Analysis 或 Report Validation 失败：不得写文件、commit、push 或发送邮件。
- 日报写入或 diff gate 失败：不得 commit、push 或发送邮件。
- commit 失败：不得 push 或发送邮件。
- commit 成功但 push 失败：只核验并重试原 commit 的 push，不重新生成或重新 commit。
- push 成功但邮件失败：只重建同一日报 Revision 的 Email Summary Projection 并重试投递。
- 已成功归档或成功投递的相同 Revision 不得重复提交或重复发送。
- 失败恢复不得降低来源、Evidence、Region、路径、分支、敏感信息或安全门禁。

---

## 10. 本节点明确不做

本 A11 治理节点不：

- 运行真实 Global / China AI News 任务；
- 生成、写入或提交真实日报；
- 发送真实日报邮件；
- 创建空的 `每日AI资讯` 目录；
- 修改 Stage 1.1–1.11 `FROZEN` 历史正文；
- 删除或迁移旧 `reports/**` 历史；
- 修改 `pyproject.toml`、lockfile、Source Config 或 State 数据；
- 创建 GitHub Actions、cron、launchd、daemon、OpenAI API 或 `LLMProvider`；
- push、checkout、merge 或修改 `main`；
- 创建或启动新的真实定时任务。

---

## 11. 冻结结论

- `AUTOMATION_AI_NEWS_WRITE_GATE = READY`。
- `AUTOMATION_MAIN_WRITE_GATE = NOT READY`。
- Current Personal MVP 模式为 `UNATTENDED_WRITE`。
- 唯一 Git 目标为 `AI_News` / `origin/AI_News`。
- 唯一新日报目标为 `06_研究与探索/每日AI资讯/*_Global_AI_News.md` 或 `*_China_AI_News.md` 的对应 Region 合法日期文件。
- Gmail 只在成功 push 后投递摘要，收件人和凭证不进入仓库。
- Stage 1.1–1.11 未被本文件明确 supersede 的全部规则继续有效。
