# Codex AI Intelligence · 运行规范入口 · v0.3

内部版本：`v0.3`

文档性质：Stage 1.12 A8–A9 Codex 情报执行规范入口

状态：`ACTIVE`

文档更新时间：`2026-08-15 15:31`（Asia/Shanghai）

> 本目录定义未来 Codex Automation 执行 AI 情报研究时的可复用、可审核任务契约。
> 当前建立 Codex 运行规范与人工单次执行合同，不创建 Codex Automation，也不构成 Eterna 正式产品定义、上位承诺或无人值守写入授权。

---

## 路线与边界

当前目标是每天两次、由个人使用的 AI intelligence MVP。Codex 在受控任务内承担 research、analysis 与 orchestration，因此当前路线采用 Codex Task / Skill，不新增 OpenAI API `LLMProvider` 集成层。

[Stage 1.12 Personal MVP Route Amendment](../../Stage1/Stage_1.12_Personal_MVP_Route_Amendment_v0.1.md) 是该调整的正式治理依据。它只对当前 Personal MVP 的调度平台、LLM runtime 和 Stage 1.12 后续实现顺序做局部 supersede，不修改 Stage 1.1–1.11 的历史正文。Stage 1.10 / 1.11 的 GitHub Actions、Python Pipeline 与 `LLMProvider` 方案继续作为 Future Production Route 保留。

- Codex：未来负责在明确授权的任务中检索、核验、分析、编排与输出。
- A1–A7 Python 基础：继续提供 Config、Source Registry 门禁、Collector、Normalizer、CandidateItem、Evidence、事件聚类和 State 的确定性治理与审计能力，并可作为后续 Codex 工具；单次 Codex 任务不被强制要求运行完整 Python Pipeline。
- `reports/**`：未来正式日报的唯一归档区域；A8 不写入该区域。
- Git 与 Gmail：仅保留未来顺序与边界，实际能力由后续独立节点批准和实现。

不得把个人 ChatGPT / Codex Cookie、Session、订阅额度或网页登录状态包装成程序 API，也不得在仓库内写入 API Key、Secret 或账号信息。

---

## 文件关系

- [Personal MVP Route Amendment](../../Stage1/Stage_1.12_Personal_MVP_Route_Amendment_v0.1.md)：当前 Personal MVP 路线调整及权威优先级。
- [AI Intelligence Shared Skill](AI_Intelligence_Skill.md)：Global / China 共用的研究、证据、状态、去重、价值提取与安全规则。
- [Global Task](Global_Task.md)：未来 Global AI Intelligence 独立任务契约。
- [China Task](China_Task.md)：未来 China AI Intelligence 独立任务契约。
- [Single-Run Execution Contract](Single_Run_Execution.md)：A9 人工单次运行的输入、门禁、Research、Report、Git、Gmail 与失败处理合同。

运行时必须先读取 Amendment，再读取 Shared Skill、对应 Region Task 与 Single-Run Execution Contract，随后加载未被 supersede 的 Stage 1 `FROZEN` 规则和 Source Registry；不得把两条链合并执行。

---

## 计划执行配置

- Global：每日 `08:00 Asia/Shanghai`。
- China：每日 `20:00 Asia/Shanghai`。
- 计划模型档位：`Luna High`。创建真实 Automation 前必须按当时官方文档和当前账号实际可选项重新核验准确名称、档位与可用性，不得静默替换模型或降低治理标准。

OpenAI 官方的 [GPT-5.6 Luna model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) 当前记录 `high` reasoning effort，但这不证明特定 Codex Automation 或账号届时可选；A8 Fix 不创建 API 调用、凭证或模型配置。

---

## 人工单次执行

A9 只验证一次由用户明确批准、人工触发的 Region 任务。规范文件与正式日报必须分开提交；日报完成验证、commit 且 push 后，才可探测并使用当前已授权的 Gmail 能力。`AUTOMATION_MAIN_WRITE_GATE = NOT READY` 继续有效。

---

## 后续节点

后续节点可在独立批准后创建 Codex Automation、Git 归档和 Gmail 投递能力。所有后续实现必须遵守 Amendment，以及 Stage 1.1–1.11 中未被明确 supersede 的合规、幂等、Region 隔离、写入路径和敏感信息边界。
