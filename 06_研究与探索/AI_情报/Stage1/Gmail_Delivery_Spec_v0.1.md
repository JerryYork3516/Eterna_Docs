# AI 情报自动化系统 · Gmail Delivery Spec · Stage 1.9 · v0.1

内部版本：`v0.1`

文档性质：AI 情报 Gmail 邮件摘要与投递规范

状态：`FROZEN`

文档更新时间：`2026-08-11 22:24`（Asia/Shanghai）

> 本文件只冻结 Global / China AI 情报日报对应的邮件摘要、主题、投递状态、修订与检索规则。
> 本文件属于研究/工程规划，不构成 Gmail 接入、账号授权、发送实现、自动化方案或 Eterna 上位承诺。

---

## 1. 适用范围与继承边界

- 本规范位于 `06_研究与探索/AI_情报`，继承 Stage 1.1–1.8 的事实、状态、来源、价值提取、日报格式与存储边界。
- Docs 中的 Markdown 日报是长期研究归档；Email 只是对应日报的通知与摘要投影。
- Email 不成为新的事实源、Evidence、IntelligenceEvent 或正式研究归档。
- 本节点不修改 Stage 1.1–1.8 或任何 Eterna 上位 `FROZEN` 文档，不改变 Eterna 正式定义。
- 本节点不连接 Gmail，不实现投递，不测试 ChatGPT Gmail Connector，也不开始 Stage 1.10。

---

## 2. Email 与 Docs 日报的权威关系

```text
IntelligenceReport
↓
Markdown Daily Report
↓
Email Summary Projection
↓
Gmail
↓
ChatGPT / User
```

规则：

- Email 必须由一份确定的 Markdown Daily Report 投影生成，不得脱离日报独立形成情报结论。
- Email 不得包含对应 Docs 日报中不存在的新事实、事件、状态或 Eterna 判断。
- Email 不得修改 Event 的 `Status`、`Confidence`、`Importance`、`Why it matters` 或 Eterna 价值等级。
- Email 可以压缩展示，但不得通过省略关键不确定性改变原意。
- Email 与日报内容冲突时，以对应 Revision 的 Docs 日报及其 Evidence 追溯链为准。
- Email 中的来源链接只是日报 Evidence 的必要投影，不替代完整追溯链。

---

## 3. 确定性邮件主题

### 3.1 正常主题

- Global：`[Eterna AI Intelligence] Global | YYYY-MM-DD`
- China：`[Eterna AI Intelligence] China | YYYY-MM-DD`

### 3.2 Failed 主题

- Global：`[Eterna AI Intelligence] Global | YYYY-MM-DD | FAILED`
- China：`[Eterna AI Intelligence] China | YYYY-MM-DD | FAILED`

### 3.3 Revision 主题

- Global：`[Eterna AI Intelligence] Global | YYYY-MM-DD | Revision rN`
- China：`[Eterna AI Intelligence] China | YYYY-MM-DD | Revision rN`

主题规则：

- 固定前缀必须为 `[Eterna AI Intelligence]`，不得使用随机标题。
- Region 只允许 `Global` 或 `China`，不得互换、缩写或合并。
- 日期必须是对应日报的 `report_date`，不得使用邮件发送日期替代。
- 首次正常投递不添加随机后缀；Failed 与正式 Revision 只使用本节规定的后缀。
- 主题的前缀、Region 和日期顺序必须稳定，以支持 Gmail 与 ChatGPT 检索。

---

## 4. 邮件头部元数据

正常、Partial、No valid report 与 Revision 邮件正文顶部至少包含：

```text
Report Date: YYYY-MM-DD
Region: Global | China
Report Status: Generated | Partial | No valid report
Coverage: <coverage_started_at> → <coverage_ended_at>
Generated At: <report_generated_at>
Revision: rN
Docs Report: <repository path or accessible report URL>
```

- `Report Date`、`Coverage`、`Generated At` 与 `Revision` 必须与对应 Docs 日报一致。
- `Docs Report` 必须指向 Stage 1.8 规范路径中的对应日报，或该日报的可访问仓库链接。
- 邮件发送时间不替代 `Report Date`、`Coverage` 或 `Generated At`。
- Email 不新增独立事件时间；来源发布时间继续以 Docs 日报及 Evidence 为准。

Failed 通知只使用第 9 节规定的最小元数据，不伪装成正常摘要。

---

## 5. 正常邮件正文结构

```markdown
# AI Intelligence Summary

## 今日核心摘要

## 最重要事件

### <Event 1 标准标题>
- What happened：<日报摘要投影>
- Status：Confirmed | High-confidence signal | Unconfirmed | Community trend
- Confidence：High | Medium | Low
- Importance：Critical | High | Medium | Low
- Why it matters：<日报内容投影>
- Primary Source：<一手来源名称与公开 URL>
- Contradicts：<有冲突时明确提示；无则省略>

## Eterna 价值提取

### 直接有用

### 值得跟踪

### 风险 / 竞争信号

### Eterna 今日主控判断

## 完整日报

Docs：<report path or accessible URL>
```

- 邮件保持高信息密度，不复制完整日报或完整 Evidence 链。
- 固定正文标题不得随机改名；无内容时保留标题并明确写明“无”。
- `Primary Source` 至少保留最主要的一手公开来源；没有一手来源时必须明确说明，不得伪造。
- 完整证据、Near Duplicate、补充来源、来源覆盖统计与 Revision History 继续保留在 Docs 日报中。

---

## 6. 最重要事件选择规则

邮件只选择对应日报中最值得优先阅读的少量 IntelligenceEvent：

- 优先选择 `Importance` 较高的 Event，并遵守 Stage 1.6 的日报排序边界。
- 每个 Event 必须保留 `Status`、`Confidence`、`Importance`、`What happened`、`Why it matters` 与主要来源。
- 不得因邮件篇幅省略会改变结论的限制、不确定性或条件。
- `Unconfirmed` 不得改写为确定事实；`High-confidence signal` 与 `Community trend` 也必须显式标记。
- 存在影响核心陈述的 `Contradicts` Evidence 时，邮件必须提示冲突；完整冲突链留在 Docs 日报。
- 不展示全部 Near Duplicate，不复制所有低重要度 Event，也不把来源或讨论数量误作事实强度。
- Email 选择不会改变日报中的 Event 排序、状态、Confidence 或 Importance。

---

## 7. Eterna 价值提取投影

邮件 Eterna 区块必须继承 Stage 1.7 / 1.8，至少显示：

- `直接有用`；
- `值得跟踪`；
- 主要风险、竞争或 Provider 信号；
- `Eterna 今日主控判断`。

必要时可引用影响域、Current-stage fit 与依据，但不得形成日报之外的新判断。“Eterna 今日主控判断”仍然只是研究摘要，不得自动：

- 修改路线或正式定义；
- 创建开发、工程或研究任务；
- 调整当前 Stage；
- 替换模型或 Provider；
- 修改 ADR、产品计划或任何 `FROZEN` 文档。

---

## 8. Generated、No valid report 与 Partial

### 8.1 Generated

- 使用正常主题与完整摘要结构。
- `Report Status: Generated` 只表示对应日报有效，不表示来源覆盖为 100%。

### 8.2 No valid report

- 仍允许按正常主题投递，头部明确 `Report Status: No valid report`。
- “今日核心摘要”必须写明：

> 本时间窗口无达到日报准入标准的重要新增事件。

- 可以显示对应日报已经记录的来源覆盖情况、少量值得跟踪信号和 Eterna 今日主控判断。
- 不得为形成邮件内容而降低 Stage 1.6 日报准入标准，也不得加入 Docs 日报不存在的信号。

### 8.3 Partial

- 使用正常主题，头部必须明确 `Report Status: Partial`。
- 正文必须简要说明缺失的关键来源、是否存在 P0 来源不可用，以及缺口对本次结论的影响。
- 不得暗示来源覆盖完整，不得用邮件摘要隐藏 Docs 日报中的覆盖缺口。

---

## 9. Failed 报告通知

当对应日报状态为 `Failed` 时，不得生成正常新闻摘要。允许发送最小故障通知：

```text
# AI Intelligence Delivery Notice

Report Date: YYYY-MM-DD
Region: Global | China
Report Status: Failed
Coverage: <coverage_started_at> → <coverage_ended_at>
Revision: rN
Failure Reason: <可公开记录的简要原因>
Docs Report: <report path / URL | Not generated>
```

- 使用本规范的 `| FAILED` 主题。
- 不伪造 Event、摘要、来源覆盖或 Eterna 价值判断。
- 不得使用历史日报冒充本业务日期日报。
- 失败原因只保留可公开记录的最小必要信息，不包含凭证、内部调试秘密或账号信息。
- 失败不得触发降低采集、事实、合规或安全规则的降级路径。

---

## 10. 正式 Revision 邮件

Stage 1.8 日报发生正式 Revision 时，可以发送对应修订邮件。主题使用 `| Revision rN`，正文顶部必须增加：

```text
Previous Revision: rN-1
Current Revision: rN
Revision Reason: <原因>
Material Changes: <主要变化>
```

规则：

- Revision 邮件只投影当前正式修订，不静默发送看起来与旧邮件相同的新邮件。
- 修订原因与主要变化必须和 Docs 日报的 Revision History 一致。
- 旧邮件不删除；新邮件通过主题与元数据明确其修订身份。
- Revision 不得删除、伪造或隐藏历史来源、旧状态或冲突 Evidence。

---

## 11. 投递状态与幂等语义

### 11.1 投递状态

投递状态与 `Report Status` 是不同概念：

| Delivery Status | 语义 |
| --- | --- |
| `Not attempted` | 对该报告 Revision 尚未尝试正式投递。 |
| `In progress` | 正在进行一次正式投递尝试；不表示成功。 |
| `Delivered` | 官方支持的发送服务已接受本次投递；不等于用户已打开或阅读。 |
| `Delivery failed` | 本次投递未成功；Docs 日报状态与内容不受影响。 |

本节点只冻结状态语义，不定义状态存储、message-id、数据库或发送服务返回值映射。

### 11.2 幂等规则

- 同一 `(Region, report_date, revision)` 只允许一次正式成功投递。
- 自动化重试必须复用同一逻辑投递身份，不得产生多封重复正式邮件。
- `Delivery failed` 可以安全重试；只有成功进入 `Delivered` 后才算正式投递完成。
- 新的正式 Revision 使用新的 revision，因此可以形成一封明确标记的修订邮件。
- 重试不得修改主题、正文事实、Event 判断、Eterna 价值或对应 Docs 日报。
- 本节点不定义具体幂等键、Gmail message-id、数据库、锁或实现算法。

---

## 12. 投递失败边界

邮件发送失败：

- 不影响 Docs 日报已经生成和归档的事实；
- 不删除、覆盖或回滚 Docs 日报；
- 不重复生成 IntelligenceEvent、摘要或 Eterna 价值提取；
- 允许在相同逻辑投递身份下安全重试；
- 不重新执行采集、去重、聚类或分析链；
- 不改变 Event 的事实、状态、Confidence、Importance 或 Eterna 判断；
- 不触发绕过 Gmail、Google、OpenAI 或平台安全机制的降级方案。

---

## 13. Global / China 隔离

- Global Email 只能基于对应 Global Report。
- China Email 只能基于对应 China Report。
- 一封邮件不得混合两份日报，不得加入另一个 Region 的 Event、摘要、来源或价值提取。
- 两类邮件分别维护主题、report_date、Coverage、Revision、Docs Report 与投递状态。

---

## 14. ChatGPT Gmail 可检索性

为支持后续稳定检索，每封邮件必须保持：

1. 固定主题前缀：`[Eterna AI Intelligence]`。
2. 固定 Region：`Global` 或 `China`。
3. 固定业务日期：`YYYY-MM-DD`。
4. 固定正文标题：`今日核心摘要`、`最重要事件`、`Eterna 价值提取`、`完整日报`。
5. 固定头部字段名：`Report Date`、`Region`、`Report Status`、`Coverage`、`Generated At`、`Revision`、`Docs Report`。

该结构应支持未来按主题前缀、Region、日期和正文标题定位单日或时间范围内的邮件，并比较多封邮件中的 Eterna 价值提取。

本节点只冻结可检索结构，不连接 Gmail，不验证 Gmail 搜索行为，也不实际测试 ChatGPT Gmail Connector。可检索性目标不构成对未来 Connector 具体能力或结果的保证。

---

## 15. 收件人与隐私边界

- 正式收件人只定义为用户后续指定的 Gmail 地址，本文件不记录任何真实邮箱地址。
- 收件人地址只能在后续获批实现中通过受保护的 Secret 或私有配置提供，不得硬编码进公开仓库。
- 不得将 OAuth Token、Refresh Token、App Password、API Key、Cookie、Session、账号密码或 ChatGPT / Codex 凭证写入 Docs。
- 不共享 ChatGPT、Codex、Google 或 Gmail 账号，不把 Gmail 密码交给代理或代码。

---

## 16. 邮件内容与格式安全

邮件只允许包含：

- 对应日报摘要；
- 必要的公开来源链接；
- 对应日报已有的 Eterna 研究判断；
- 报告和修订元数据；
- 必要且可公开的覆盖缺口或失败说明。

邮件禁止包含：

- API Key、Cookie、Session、OAuth Token、Refresh Token、GitHub Token 或 Gmail 凭证；
- 平台登录信息、账号密码、App Password 或内部调试秘密；
- 与情报目的无关的个人信息；
- 通过绕过访问控制取得的内容。

格式要求：

- 使用 UTF-8。
- 可支持纯文本或标准 HTML，但必须提供即使 HTML 渲染失败仍可理解的文本语义。
- 不依赖复杂 CSS、图片、远程字体或专有组件表达关键内容。
- 核心摘要、状态、不确定性、来源和 Docs 链接不得只存在于图片中。

---

## 17. 合规与账号安全硬约束

- 后续只允许使用 Google 官方支持、公开且获得授权的认证与发送方式。
- 不绕过 Google 登录、验证码、多因素认证、安全验证、访问控制、Rate Limit 或账号风控。
- 不创建、借用、共享或盗用他人账号与凭证。
- 凭证只能进入受保护的 Secret 或环境变量，不得写入仓库、日志或邮件正文。
- 自动化失败不得触发规避 Google、OpenAI 或第三方平台安全机制的方案。
- 邮件投递不得改变 Stage 1.1–1.8 的公开、合法、最小必要信息边界。

---

## 18. 本节点明确不做

Stage 1.9 不做：

- 不连接 Gmail，不实际发送或测试邮件；
- 不申请 OAuth Client，不创建 Google Cloud Project；
- 不创建 App Password，不配置 SMTP，不调用 Gmail API；
- 不写发送脚本、业务代码、LLM Prompt、模型调用或 Secret；
- 不创建 GitHub Actions、cron、定时任务或自动化；
- 不实际测试 ChatGPT Gmail 读取或 Connector；
- 不写入真实邮箱地址、账号或任何凭证；
- 不修改 Stage 1.1–1.8 或任何 Eterna 上位 `FROZEN` 文档；
- 不开始 Stage 1.10。

---

## 19. Stage 1.9 验收标准

Stage 1.9 只有同时满足以下条件才可 PASS：

- Email 与 Docs 日报的权威关系明确，Email 不成为新事实源；
- Global / China 确定性主题与固定正文结构明确；
- Generated、Partial、No valid report、Failed 与 Revision 邮件语义明确；
- 最重要事件与 Eterna 价值提取投影规则完整；
- 投递状态、失败边界与 `(Region, report_date, revision)` 幂等语义明确；
- ChatGPT Gmail 可检索结构明确；
- 收件人地址和凭证不进入仓库；
- Global / China 完全隔离；
- 未进入 Gmail、OAuth、SMTP、代码、Secret 或自动化实现；
- 未修改任何 Eterna 上位 `FROZEN` 文档，未开始 Stage 1.10。
