# Codex AI Intelligence · 运行规范入口 · v0.6

内部版本：`v0.6`

文档性质：Stage 1.12 A8–A11 Codex 情报执行规范入口

状态：`ACTIVE`

文档更新时间：`2026-08-15 22:08`（Asia/Shanghai）

> 本目录定义 Codex Automation 执行 AI 情报研究时的可复用、可审核任务契约。
> A11 已将两条 Current Personal MVP Automation 治理模式升级为受限 `UNATTENDED_WRITE`。
> 授权只覆盖 `AI_News` 上的单一日报与成功 push 后的 Gmail 摘要，不构成 Eterna 正式产品定义或 `main` 写入授权。

---

## 路线与边界

当前目标是每天两次、由个人使用的 AI intelligence MVP。Codex 在受控任务内承担 research、analysis 与 orchestration，因此当前路线采用 Codex Task / Skill，不新增 OpenAI API `LLMProvider` 集成层。

[Stage 1.12 Personal MVP Route Amendment](../../Stage1/Stage_1.12_Personal_MVP_Route_Amendment_v0.1.md) 是该调整的正式治理依据。它只对当前 Personal MVP 的调度平台、LLM runtime 和 Stage 1.12 后续实现顺序做局部 supersede，不修改 Stage 1.1–1.11 的历史正文。Stage 1.10 / 1.11 的 GitHub Actions、Python Pipeline 与 `LLMProvider` 方案继续作为 Future Production Route 保留。

[Stage 1.12 Unattended Write and Delivery Amendment](../../Stage1/Stage_1.12_Unattended_Write_and_Delivery_Amendment_v0.1.md) 进一步只 supersede 当前日报路径、自动 Git 目标、A10 Observe-only 门禁与 Gmail capability。未被两个 Amendment 明确覆盖的 Stage 1.1–1.11 规则继续有效。

- Codex：在明确授权的任务中负责检索、核验、分析、编排与输出。
- A1–A7 Python 基础：继续提供 Config、Source Registry 门禁、Collector、Normalizer、CandidateItem、Evidence、事件聚类和 State 的确定性治理与审计能力，并可作为后续 Codex 工具；单次 Codex 任务不被强制要求运行完整 Python Pipeline。
- `06_研究与探索/每日AI资讯/**`：Current Personal MVP 正式日报的唯一新写入区域；旧 `reports/**` 只保留历史。
- Git：只允许 `AI_News` / `origin/AI_News`；`main` 写入门禁保持关闭。
- Gmail：只在对应日报成功 push 后使用已授权 capability 发送摘要；收件人由任务受保护配置提供。

不得把个人 ChatGPT / Codex Cookie、Session、订阅额度或网页登录状态包装成程序 API，也不得在仓库内写入 API Key、Secret 或账号信息。

---

## 文件关系

- [Personal MVP Route Amendment](../../Stage1/Stage_1.12_Personal_MVP_Route_Amendment_v0.1.md)：当前 Personal MVP 路线调整及权威优先级。
- [Unattended Write and Delivery Amendment](../../Stage1/Stage_1.12_Unattended_Write_and_Delivery_Amendment_v0.1.md)：A11 日报路径、`AI_News` Git 目标、`UNATTENDED_WRITE` 与 Gmail 投递门禁。
- [Source Registry Addendum](../../Stage1/Stage_1.12_Source_Registry_Addendum_v0.1.md)：Current Personal MVP 对 GitHub 官方来源的追加准入；与 Base Source Registry 共同构成当前来源权威。
- [AI Intelligence Shared Skill](AI_Intelligence_Skill.md)：Global / China 共用的研究、证据、状态、去重、价值提取与安全规则。
- [Global Task](Global_Task.md)：Global AI Intelligence 独立任务契约。
- [China Task](China_Task.md)：China AI Intelligence 独立任务契约。
- [Single-Run Execution Contract](Single_Run_Execution.md)：A9 人工单次运行的输入、门禁、Research、Report、Git、Gmail 与失败处理合同。
- [Automation Safety Gate](Automation_Safety_Gate.md)：A11 `UNATTENDED_WRITE` 的路径、Git、Gmail 与失败恢复门禁。

Current Personal MVP 的 structured Event identity 必须由 `pipeline/event_anchor.py` 对 Evidence 支持的结构化字段进行确定性生成；Codex 自由文本只能作为 Event Label，不得作为正式 `event_anchor`。

运行时必须先读取 A11 Amendment 与 Personal MVP Route Amendment，再读取 Shared Skill、对应 Region Task 与 Single-Run Execution Contract，随后加载未被 supersede 的 Stage 1 `FROZEN` 规则、Base Source Registry 及当前有效 Addendum；不得把两条链合并执行。

---

## 计划执行配置

- Global：每日 `08:00 Asia/Shanghai`。
- China：每日 `20:00 Asia/Shanghai`。
- 计划模型档位：`Luna High`。创建真实 Automation 前必须按当时官方文档和当前账号实际可选项重新核验准确名称、档位与可用性，不得静默替换模型或降低治理标准。

OpenAI 官方的 [GPT-5.6 Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) 当前记录 `high` reasoning effort，但这不证明特定 Codex Automation 或账号届时可选；A8 Fix 不创建 API 调用、凭证或模型配置。

---

## 单次执行与副作用顺序

A9 合同同时约束人工与已批准 Automation 的单 Region 运行。正式顺序为 Research → Evidence Verification → deterministic Event Anchor → Analysis → Eterna Value Extraction → Report → Validation → 日报写入 → diff gate → commit → push `origin/AI_News` → Gmail Summary。任何前序步骤 FAIL，禁止后续副作用。

---

## A11 Unattended Write Automation

- `Eterna Global AI Intelligence`：每日 `08:00 Asia/Shanghai`，`gpt-5.6-luna / high`，`UNATTENDED_WRITE`。
- `Eterna China AI Intelligence`：每日 `20:00 Asia/Shanghai`，`gpt-5.6-luna / high`，`UNATTENDED_WRITE`。
- Global 路径：`06_研究与探索/每日AI资讯/YYYY-MM-DD_Global_AI_News.md`。
- China 路径：`06_研究与探索/每日AI资讯/YYYY-MM-DD_China_AI_News.md`。
- `AUTOMATION_AI_NEWS_WRITE_GATE = READY`；`AUTOMATION_MAIN_WRITE_GATE = NOT READY`。
- State、FROZEN、INDEX、CHANGELOG、配置、其他分支与其他文件仍全部拒绝。

---

## Gmail 与安全边界

邮件只在成功 push 后投影最重要 `3–5` 条、Eterna 价值、今日主控判断与其他 News 简要摘要，不附加 Markdown、不复制整份日报。邮件失败只重试 Email Delivery。真实收件人、OAuth、Token、Cookie、Session 和账号信息不得进入仓库。

本次 A11 只修治理与确定性门禁，不运行真实 Automation、不生成真实日报、不发送真实邮件、不创建空目录，也不修改 Stage 1.1–1.11 `FROZEN` 正文。
