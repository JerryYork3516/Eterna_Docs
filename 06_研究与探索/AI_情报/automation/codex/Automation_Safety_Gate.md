# Codex AI Intelligence · Automation Safety Gate · Stage 1.12 A10/A11 · v0.2

内部版本：`v0.2`

文档性质：Codex Automation 无人值守安全与副作用门禁

状态：`ACTIVE`

文档更新时间：`2026-08-15 22:08`（Asia/Shanghai）

> A11 将 Current Personal MVP 从 Observe-only 升级为受限 `UNATTENDED_WRITE`。
> 授权只覆盖 `AI_News` 上的单一 Region 日报与成功 push 后的 Gmail 摘要；本次治理变更不运行真实任务或发送邮件。

---

## 当前门禁

```text
AUTOMATION_MAIN_WRITE_GATE = NOT READY
AUTOMATION_AI_NEWS_WRITE_GATE = READY
```

- `branch` 必须严格等于 `AI_News`。
- `upstream` 必须严格等于 `origin/AI_News`。
- `main` 永远不是当前 Automation 写入目标。
- 任一 Git 目标、工作区、HEAD、路径或前序执行条件不一致时必须 fail closed。

### UNATTENDED_WRITE

Stage 1.12 A11 当前唯一允许的无人值守模式。

只允许完整链：

```text
Research
→ Evidence Verification
→ Dedup / deterministic Event Anchor
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

任何前序步骤 FAIL，禁止继续后续副作用。

允许写入：

```text
Global: 06_研究与探索/每日AI资讯/YYYY-MM-DD_Global_AI_News.md
China:  06_研究与探索/每日AI资讯/YYYY-MM-DD_China_AI_News.md
```

- 每次只允许当前 Region、当前业务日期、当前 Revision 的一个正式日报文件。
- Global 不能写 China 文件，China 不能写 Global 文件。
- 第一份真实日报写入时才按需创建 `每日AI资讯` 目录，不预建空目录。
- 旧 `06_研究与探索/AI_情报/reports/**` 只保留历史，不是当前写入目标。

禁止：

- push、checkout、merge 或修改 `main`；
- force push、改写历史或创建其他分支；
- 修改 Stage 1.1–1.11 `FROZEN`、INDEX、CHANGELOG、AGENTS、配置或规则；
- 写 `automation/state/**` 或日报之外的任何文件；
- 删除或迁移旧 `reports/**` 历史；
- 暂存、提交、覆盖或清理人工修改；
- 创建 Secret、OpenAI API / `LLMProvider`、GitHub Actions 或其他 scheduler；
- 因来源、日期、证据、Event Anchor、路径、分支或治理条件不足而降低安全标准。

---

## Git 门禁

提交前必须确认：

- repo 为 `JerryYork3516/Eterna_Docs`；
- branch / upstream 为 `AI_News` / `origin/AI_News`；
- working tree 在本次报告写入前 clean；
- diff 只有当前 Region、当前日期日报；
- 路径、日期、Region、Report Status、Revision、固定章节、Evidence 和敏感信息校验 PASS；
- 没有 State、FROZEN、INDEX、CHANGELOG、AGENTS、配置或其他文件变化。

确定性 commit message：

```text
intel: add Global AI news YYYY-MM-DD
intel: add China AI news YYYY-MM-DD
intel: revise Global AI news YYYY-MM-DD rN
intel: revise China AI news YYYY-MM-DD rN
```

一次自动 commit 只能包含一个日报。无有效变化时不得创建空 commit。push 目标只能是 `origin AI_News`。

---

## Gmail 门禁

当前 Gmail capability 已由用户连接并人工测试成功。Automation 只有在对应日报 commit 且成功 push 到 `origin/AI_News` 后才可使用该已授权 capability。

邮件只投影：

- 最重要 `3–5` 条；
- Event 状态、Confidence、Importance、关键不确定性和主要公开来源；
- Eterna 价值提取与今日主控判断；
- 其他 News 简要摘要；
- 对应日报路径与 Revision。

邮件不发送 Markdown 附件，不复制整份日报，不引入日报之外的新事实或判断。

收件人由 Codex Automation 任务受保护配置提供。Proton 收件地址、其他真实邮箱地址、OAuth、Token、Cookie、Session、密码和账号信息不得写入仓库。

同一 `(Region, report_date, revision)` 不得重复成功投递。邮件失败只报告或重试 Email Delivery；不得重新 Research、重新生成日报、重新 commit 或重新 push。

---

## Automation 登记

| Name | Region | Schedule | Model / Reasoning | Mode | Status |
| --- | --- | --- | --- | --- | --- |
| Eterna Global AI Intelligence | `Global` | 每日 `08:00 Asia/Shanghai` | `gpt-5.6-luna` / `high` | `UNATTENDED_WRITE` | `ACTIVE / WRITE GATED` |
| Eterna China AI Intelligence | `China` | 每日 `20:00 Asia/Shanghai` | `gpt-5.6-luna` / `high` | `UNATTENDED_WRITE` | `ACTIVE / WRITE GATED` |

- Global 与 China 的来源、Event、日报、commit 和邮件完全独立。
- 本文件只更新仓库治理合同，不实际运行、重建或修改 Automation 任务配置。
- 当前收件人值只存在于任务受保护配置，不在仓库内登记。

---

## 失败与重试

- Research / Verification / Analysis / Report Validation 失败：不得写文件、commit、push 或发送邮件。
- 写入或 git diff gate 失败：不得 commit、push 或发送邮件。
- commit 失败：不得 push 或发送邮件。
- commit 成功但 push 失败：只核验并重试原 commit 的 push。
- push 成功但 Gmail 失败：只重建同一日报 Revision 的 Email Summary Projection 并重试投递。
- 已成功归档或投递的同一 Revision 不得重复 commit、push 或发送。

---

## 每次运行输出合同

每次运行至少返回：

- Region、Actual Started At、Report Date、Coverage Window 与 Revision；
- Research / Verification / Analysis / Report Validation 结果；
- Event Count、Source Coverage / Gaps 与 Eterna Value Extraction；
- Report Path、Path Policy 与 Git Diff Gate；
- Branch / Upstream、Commit SHA 与 Push 结果；
- Gmail capability、Delivery Status 与幂等身份；
- `AUTOMATION_AI_NEWS_WRITE_GATE = READY`；
- `AUTOMATION_MAIN_WRITE_GATE = NOT READY`；
- working tree 与 local / upstream / remote HEAD 对账。

---

## 本节点执行边界

A11 本次只修仓库治理与确定性门禁：

- 不运行 Global / China Automation；
- 不生成、写入、commit 或 push 真实日报；
- 不发送真实日报邮件；
- 不创建空目录、Workflow、cron、launchd、daemon、OpenAI API 或 `LLMProvider`；
- 不修改 macOS 电源设置；
- 不修改 Stage 1.1–1.11 `FROZEN` 历史正文；
- 不修改 `main` 或 merge `AI_News` 到 `main`。
