# China AI Intelligence · Codex Task Specification · v0.3

内部版本：`v0.3`

文档性质：Stage 1.12 A8 China 独立任务规范

状态：`ACTIVE`

文档更新时间：`2026-08-15 22:08`（Asia/Shanghai）

> 定义 Current Personal MVP China AI Intelligence Codex Automation 的单次任务合同。
> A11 已批准受限 `UNATTENDED_WRITE`；本次治理变更不运行真实任务、不生成日报或发送邮件。

---

## 运行合同

- 必须先读取 [Unattended Write and Delivery Amendment](../../Stage1/Stage_1.12_Unattended_Write_and_Delivery_Amendment_v0.1.md) 与 [Personal MVP Route Amendment](../../Stage1/Stage_1.12_Personal_MVP_Route_Amendment_v0.1.md)，再读取 [Codex AI Intelligence Shared Skill](AI_Intelligence_Skill.md) 与本 China Task，随后加载 Stage 1 `FROZEN` 规则和 Source Registry。
- `Region` 固定为 `China`，不得采集或生成 Global Event。
- 计划调度为每日 `20:00 Asia/Shanghai`。
- 每次运行必须由调用方显式提供 `report_date`、`coverage_started_at`、`coverage_ended_at` 与 `revision`。
- 来源范围以 Source Registry 的 China 条目为准，优先 P0 / P1 官方主体和 builders。
- 目标路径固定为：

```text
06_研究与探索/每日AI资讯/YYYY-MM-DD_China_AI_News.md
```

- Git 目标固定为 `branch = AI_News`、`upstream = origin/AI_News`。
- commit message 为 `intel: add China AI news YYYY-MM-DD`；Revision 为 `intel: revise China AI news YYYY-MM-DD rN`。
- 只有该日报成功 push 到 `origin/AI_News` 后才可发送 China Gmail 摘要。

---

## 重点范围

重点关注 DeepSeek、阿里 Qwen、字节 Seed / 豆包、智谱 GLM / Z.ai、Moonshot / Kimi、MiniMax、腾讯混元、百度文心、华为盘古、国内开源社区、国内主流 AI 产品变化、国内 builders / 官方账号公开信号，以及 Source Registry 后续合法登记的重要中国 AI 主体。

微博、知乎、B站、抖音、小红书、微信公众号等公开社区只能在合法公开、无需绕过访问控制的条件下用于发现趋势或实测信号。无法合法稳定访问时必须放弃或使用合法替代方案，不得采用登录模拟、私有 API、Cookie、逆向接口或反爬绕过。

---

## 执行步骤

1. 按 A11 Amendment → Personal MVP Route Amendment → Shared Skill → China Task → Stage 1 `FROZEN` → Source Registry 的读取顺序核对任务参数和权威边界。
2. 只载入 China 来源，并对覆盖窗口做明确记录。
3. 优先检查官方模型、产品、API、研究、公司发布、官方仓库和核心人物公开动态。
4. 按需覆盖 AI Coding、Agent、Voice / STS、Multimodal、Robotics / Embodied AI、Open Source、Infrastructure、Research、Product 与 Business / Ecosystem。
5. 仅以合法搜索或公开页面发现社区趋势；打开可访问的实际来源，搜索摘要不能作为唯一事实依据。
6. 区分事实、来源表述、Codex 推断、传闻和社区趋势，并使用四种固定 Information Status。
7. 执行 Exact / Near / Same Event 规则；Same Event 必须具有明确事件实例锚点并保留全部 Evidence。
8. 对高重要度事件做有限交叉核验，暴露来源覆盖缺口、平台限制和冲突证据。
9. 按 Stage 1.8 生成 China 独立日报草案，并在结尾生成固定结构的 Eterna 价值提取。
10. 校验 Region、覆盖窗口、来源追溯、状态、重复、Prompt Injection、敏感信息、目标路径和 `AI_News` Git 目标；通过后只写该日报、commit、push，并在 push 成功后发送摘要。

---

## 验收门禁

- China / Global 没有混合来源、Event 或文件。
- 每个事实判断可以追溯至合法取得的公开来源。
- 社区与封闭平台覆盖不足被明确暴露，不通过违规方式补足。
- P3 不单独支撑 `Confirmed`，未确认或冲突内容未被写成已确认事实。
- 报告结构、状态、Revision 和 Eterna 价值提取符合 Shared Skill 与 Stage 1.8。
- 无有效事件时按 `No valid report` 语义生成合规空日报，不虚构内容。
- 写入 diff 只能包含当前日期 China 日报；禁止 State、治理、配置、Global 路径或其他文件。
- `main` 写入必须拒绝；Gmail 必须晚于 `origin/AI_News` push 成功。

---

## 当前治理变更明确不做

本次 A11 治理变更不运行本任务、不访问真实新闻来源、不创建 `每日AI资讯` 目录或日报、不发送真实 Gmail，也不调用 OpenAI API、修改 State、创建 Workflow 或触碰 `main`。
