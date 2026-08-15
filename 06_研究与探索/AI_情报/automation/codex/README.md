# Codex AI Intelligence · 运行规范入口 · v0.1

内部版本：`v0.1`

文档性质：Stage 1.12 A8 Codex 情报执行规范入口

状态：`ACTIVE`

文档更新时间：`2026-08-15 12:36`（Asia/Shanghai）

> 本目录定义未来 Codex Automation 执行 AI 情报研究时的可复用、可审核任务契约。
> 当前仅建立规范，不创建 Codex Automation，不执行网络情报采集，不生成日报，也不构成 Eterna 正式产品定义或上位承诺。

---

## 路线与边界

当前目标是每天两次、由个人使用的 AI intelligence MVP。Codex 已能在一个受控任务内承担 research、analysis 与 orchestration，因此 Stage 1.12 A8 将入口调整为 Codex Task / Skill 规范，不再新增 OpenAI API `LLMProvider` 集成层。此调整不改写 Stage 1.1–1.11 的 `FROZEN` 正文，也不删除或重构 A1–A7 已有能力。

- Codex：未来负责在明确授权的任务中检索、核验、分析、编排与输出。
- A1–A7 Python 基础：继续提供 Config、Source Registry 门禁、Collector、Normalizer、CandidateItem、Evidence、事件聚类和 State 的确定性治理与审计能力，并可作为后续 Codex 工具；单次 Codex 任务不被强制要求运行完整 Python Pipeline。
- `reports/**`：未来正式日报的唯一归档区域；A8 不写入该区域。
- Git 与 Gmail：仅保留未来顺序与边界，实际能力由后续独立节点批准和实现。

不得把个人 ChatGPT / Codex Cookie、Session、订阅额度或网页登录状态包装成程序 API，也不得在仓库内写入 API Key、Secret 或账号信息。

---

## 文件关系

- [AI Intelligence Shared Skill](AI_Intelligence_Skill.md)：Global / China 共用的研究、证据、状态、去重、价值提取与安全规则。
- [Global Task](Global_Task.md)：未来 Global AI Intelligence 独立任务契约。
- [China Task](China_Task.md)：未来 China AI Intelligence 独立任务契约。

运行时必须先读取 Shared Skill，再读取对应 Region Task；不得把两条链合并执行。

---

## 计划执行配置

- Global：每日 `08:00 Asia/Shanghai`。
- China：每日 `20:00 Asia/Shanghai`。
- 计划模型档位：`Luna High`，即以 `gpt-5.6-luna` 与 `high` reasoning effort 为当前规划基线；创建真实 Automation 前必须按当时官方可用性重新核验，不得静默替换模型或降低治理标准。

该规划依据 OpenAI 官方的 [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/latest-model) 与 [GPT-5.6 Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna)。A8 不创建 API 调用、凭证或模型配置。

---

## 后续节点

后续节点可在独立批准后创建 Codex Automation、Git 归档和 Gmail 投递能力。所有后续实现仍须继承 Stage 1.1–1.11 的合规、幂等、Region 隔离、写入路径和敏感信息边界。
