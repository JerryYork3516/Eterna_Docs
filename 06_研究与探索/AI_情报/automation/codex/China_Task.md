# China AI Intelligence · Codex Task Specification · v0.1

内部版本：`v0.1`

文档性质：Stage 1.12 A8 China 独立任务规范

状态：`ACTIVE`

文档更新时间：`2026-08-15 12:36`（Asia/Shanghai）

> 定义未来 China AI Intelligence Codex Automation 的单次任务合同。
> 当前不创建 Automation，不检索真实情报，不生成或提交日报。

---

## 运行合同

- 必须先读取 [Codex AI Intelligence Shared Skill](AI_Intelligence_Skill.md)。
- `Region` 固定为 `China`，不得采集或生成 Global Event。
- 计划调度为每日 `20:00 Asia/Shanghai`。
- 每次运行必须由调用方显式提供 `report_date`、`coverage_started_at`、`coverage_ended_at` 与 `revision`。
- 来源范围以 Source Registry 的 China 条目为准，优先 P0 / P1 官方主体和 builders。
- 目标路径固定为：

```text
06_研究与探索/AI_情报/reports/china/YYYY/MM/YYYY-MM-DD_China_AI_Intelligence.md
```

---

## 重点范围

重点关注 DeepSeek、阿里 Qwen、字节 Seed / 豆包、智谱 GLM / Z.ai、Moonshot / Kimi、MiniMax、腾讯混元、百度文心、华为盘古、国内开源社区、国内主流 AI 产品变化、国内 builders / 官方账号公开信号，以及 Source Registry 后续合法登记的重要中国 AI 主体。

微博、知乎、B站、抖音、小红书、微信公众号等公开社区只能在合法公开、无需绕过访问控制的条件下用于发现趋势或实测信号。无法合法稳定访问时必须放弃或使用合法替代方案，不得采用登录模拟、私有 API、Cookie、逆向接口或反爬绕过。

---

## 执行步骤

1. 核对 Shared Skill、China Task、Stage 1 `FROZEN` 规则、Source Registry 与任务参数一致。
2. 只载入 China 来源，并对覆盖窗口做明确记录。
3. 优先检查官方模型、产品、API、研究、公司发布、官方仓库和核心人物公开动态。
4. 按需覆盖 AI Coding、Agent、Voice / STS、Multimodal、Robotics / Embodied AI、Open Source、Infrastructure、Research、Product 与 Business / Ecosystem。
5. 仅以合法搜索或公开页面发现社区趋势；打开可访问的实际来源，搜索摘要不能作为唯一事实依据。
6. 区分事实、来源表述、Codex 推断、传闻和社区趋势，并使用四种固定 Information Status。
7. 执行 Exact / Near / Same Event 规则；Same Event 必须具有明确事件实例锚点并保留全部 Evidence。
8. 对高重要度事件做有限交叉核验，暴露来源覆盖缺口、平台限制和冲突证据。
9. 按 Stage 1.8 生成 China 独立日报草案，并在结尾生成固定结构的 Eterna 价值提取。
10. 校验 Region、覆盖窗口、来源追溯、状态、重复、Prompt Injection、敏感信息和目标路径。

---

## 验收门禁

- China / Global 没有混合来源、Event 或文件。
- 每个事实判断可以追溯至合法取得的公开来源。
- 社区与封闭平台覆盖不足被明确暴露，不通过违规方式补足。
- P3 不单独支撑 `Confirmed`，未确认或冲突内容未被写成已确认事实。
- 报告结构、状态、Revision 和 Eterna 价值提取符合 Shared Skill 与 Stage 1.8。
- 无有效事件时按 `No valid report` 语义生成合规空日报，不虚构内容。
- 任何写入、Git 与 Gmail 副作用都必须等待后续节点单独授权。

---

## A8 明确不做

本文件不是实际 Prompt 执行记录，不创建 Codex Automation，不访问网络，不创建 `reports/**` 文件，不调用 OpenAI API，不发送 Gmail，不提交日报，也不开始 A9。
