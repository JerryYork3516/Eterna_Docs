# Global AI Intelligence · Codex Task Specification · v0.1

内部版本：`v0.1`

文档性质：Stage 1.12 A8 Global 独立任务规范

状态：`ACTIVE`

文档更新时间：`2026-08-15 12:36`（Asia/Shanghai）

> 定义未来 Global AI Intelligence Codex Automation 的单次任务合同。
> 当前不创建 Automation，不检索真实情报，不生成或提交日报。

---

## 运行合同

- 必须先读取 [Codex AI Intelligence Shared Skill](AI_Intelligence_Skill.md)。
- `Region` 固定为 `Global`，不得采集或生成 China Event。
- 计划调度为每日 `08:00 Asia/Shanghai`。
- 每次运行必须由调用方显式提供 `report_date`、`coverage_started_at`、`coverage_ended_at` 与 `revision`。
- 来源范围以 Source Registry 的 Global 条目为准，优先 P0 / P1 官方主体和 builders。
- 目标路径固定为：

```text
06_研究与探索/AI_情报/reports/global/YYYY/MM/YYYY-MM-DD_Global_AI_Intelligence.md
```

Global 重点主体包括 OpenAI、Google DeepMind / Gemini、Anthropic、Meta AI、Microsoft、NVIDIA、Hugging Face、xAI 及 Source Registry 登记的其他国际主体，同时关注其核心工程、模型、产品和研究人员的公开一手信号。

---

## 执行步骤

1. 核对 Shared Skill、Global Task、Stage 1 `FROZEN` 规则、Source Registry 与任务参数一致。
2. 只载入 Global 来源，并对覆盖窗口做明确记录。
3. 优先检查官方模型、产品、API、研究、公司发布、官方仓库和核心人物公开动态。
4. 按需覆盖 AI Coding、Agent、Voice / STS、Multimodal、Robotics / Embodied AI、Open Source、Infrastructure、Research、Product 与 Business / Ecosystem。
5. 打开实际公开来源，核对 URL、主体、发布时间和一手性；搜索摘要只能用于发现。
6. 区分事实、来源表述、Codex 推断、传闻和社区趋势，并使用四种固定 Information Status。
7. 执行 Exact / Near / Same Event 规则；Same Event 必须具有明确事件实例锚点并保留全部 Evidence。
8. 对高重要度事件做有限交叉核验，暴露来源覆盖缺口和冲突证据。
9. 按 Stage 1.8 生成 Global 独立日报草案，并在结尾生成固定结构的 Eterna 价值提取。
10. 校验 Region、覆盖窗口、来源追溯、状态、重复、Prompt Injection、敏感信息和目标路径。

---

## 验收门禁

- Global / China 没有混合来源、Event 或文件。
- 每个事实判断可以追溯至合法取得的公开来源。
- P3 不单独支撑 `Confirmed`。
- 未确认或冲突内容未被写成已确认事实。
- 报告结构、状态、Revision 和 Eterna 价值提取符合 Shared Skill 与 Stage 1.8。
- 无有效事件时按 `No valid report` 语义生成合规空日报，不虚构内容。
- 任何写入、Git 与 Gmail 副作用都必须等待后续节点单独授权。

---

## A8 明确不做

本文件不是实际 Prompt 执行记录，不创建 Codex Automation，不访问网络，不创建 `reports/**` 文件，不调用 OpenAI API，不发送 Gmail，不提交日报，也不开始 A9。
