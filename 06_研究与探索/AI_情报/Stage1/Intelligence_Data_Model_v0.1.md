# AI 情报自动化系统 · Intelligence Data Model · Stage 1.4 · v0.1

内部版本：`v0.1`

文档性质：AI 情报统一概念数据契约

状态：`FROZEN`

文档更新时间：`2026-08-11 15:17`（Asia/Shanghai）

> 本文件冻结 AI 情报系统 Stage 1.4 的统一概念数据模型与字段语义。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、数据库设计、Schema 实现或代码契约。

---

## 文档地位与边界

- 本文件承接 Stage 1.1 的目标与信息状态、Stage 1.2 Source Registry 的来源属性、Stage 1.3 Collection Architecture 的 Candidate Item 输出边界。
- 本节点只冻结概念数据契约与字段语义，不修改 Stage 1.1–1.3 或任何 Eterna `FROZEN` 上位文档。
- 本节点不写代码，不创建数据库，不实现 Schema、Collector、去重、聚类、分析、摘要或邮件逻辑。
- 本节点不改变 Eterna 正式定义，也不开始 Stage 1.5。

---

## 对象链与总体原则

```text
CandidateItem
↓
Evidence
↓
IntelligenceEvent
↓
IntelligenceReport
```

- 四层对象使用稳定标识与显式引用建立链路，不通过复制或改写原始证据建立关联。
- 上层对象可增加判断、摘要与价值分析，但不得覆盖下层原始字段。
- 对象字段中的“必须”表示概念契约要求，不表示已选定编程语言、数据类型、存储引擎或序列化格式。
- Global 与 China 从 CandidateItem 到 IntelligenceReport 保持独立数据链。

---

## CandidateItem

### 职责

CandidateItem 是采集后、分析前的单条标准化候选信息，用于保留 Collector 输出、Source Registry 属性和原始公开来源引用。

CandidateItem 不是事实，不是 IntelligenceEvent，也不是最终日报条目。

### 字段语义

| 字段 | 必须 | 语义与边界 |
| --- | --- | --- |
| `candidate_id` | Yes | 唯一标识该候选条目；生成算法未在本节点定义。 |
| `region` | Yes | 只允许 `Global` 或 `China`，并决定所属独立日报链。 |
| `source_reference` | Yes | 指向 Stage 1.2 Source Registry 中的已登记来源。 |
| `source_type` | Yes | 沿用 `Official`、`Person`、`Community` 或 `Media`。 |
| `source_priority` | Yes | 沿用 Source Registry 的 `P0`–`P3`，不表示该条目已确认。 |
| `source_credibility` | Yes | 沿用来源可信度，不等于事件当前可信度。 |
| `source_fact_citation` | Yes | 沿用 `Yes`、`Conditional` 或 `No` 的事实引用边界。 |
| `collector_type` | Yes | `Official API`、`RSS / Feed`、`Web Page Monitor` 或 `Search Discovery`。 |
| `source_url` | Yes | 原始公开来源 URL；不得改写为无法追溯的中间链接。 |
| `title` | Yes | 来源标题或能够识别条目的原始标题。 |
| `source_excerpt` | Conditional | 与情报分析直接相关的最小必要公开摘要或文本摘录；不得伪造正文。 |
| `source_published_at` | Conditional | 来源明确提供的发布时间；未提供时保留为未知。 |
| `collected_at` | Yes | Collector 合法获得该候选项的时间。 |
| `first_seen_at` | Yes | 系统首次观察到该候选信息的时间。 |
| `last_seen_at` | Yes | 系统最近一次观察到该候选信息的时间。 |
| `eterna_tags` | Yes | 使用本文件冻结的 Eterna 标签集合。 |
| `raw_evidence_reference` | Yes | 对原始公开页、Feed 条目、API 对象或公开搜索结果的可复核引用。 |
| `collection_status` | Yes | 只表示采集完整性，不表示信息真伪或事件状态。 |

### 采集状态

| 状态 | 语义 |
| --- | --- |
| `Collected` | 已合法获得可用的公开内容与原始引用。 |
| `Metadata only` | 只获得标题、URL、时间或搜索摘要等元数据。 |
| `Unavailable` | 原始来源当前不可合法访问；不得补造正文。 |
| `Rejected` | 条目因合规、范围或证据边界不满足要求而不进入后续分析。 |

---

## Evidence

### 职责

Evidence 是用于支持、反驳或补充某个 IntelligenceEvent 判断的可追溯证据引用。Evidence 建立候选条目与事件判断之间的明确关系，不复制或替换原始来源。

### 字段语义

| 字段 | 必须 | 语义与边界 |
| --- | --- | --- |
| `evidence_id` | Yes | 唯一标识该证据引用。 |
| `candidate_references` | Yes | 指向一个或多个 CandidateItem，不得断开对候选层的追溯。 |
| `source_reference` | Yes | 指向 Source Registry 中的来源。 |
| `source_url` | Yes | 证据对应的原始公开 URL。 |
| `source_published_at` | Conditional | 来源明确提供的发布时间，未知时不得用采集时间代替。 |
| `collected_at` | Yes | 对应 CandidateItem 的合法获取时间。 |
| `source_priority` | Yes | 来源等级 `P0`–`P3`。 |
| `source_credibility` | Yes | 来源级可信度，不是事件级结论。 |
| `is_primary_source` | Yes | 标记该证据是否为对当前事件具有一手权威的来源。 |
| `relation` | Yes | 只允许 `Supports`、`Contradicts` 或 `Supplements`。 |
| `traceability` | Yes | 记录 Evidence → CandidateItem → Source Registry → 原始 URL 的可复核链路与当前可访问性。 |
| `evidence_note` | Conditional | 只记录对关系与限制的简洁说明，不伪造来源内容。 |

### 证据关系边界

- `Supports` 表示证据支持事件的某项判断，不表示整个事件已自动 Confirmed。
- `Contradicts` 表示证据与已有判断或另一证据存在明确冲突，不得被静默丢弃。
- `Supplements` 表示证据补充时间、范围、版本或上下文。
- Evidence 关系可随新证据追加，原始来源引用不得被覆盖或伪造。

---

## IntelligenceEvent

### 职责

IntelligenceEvent 将多个相关 CandidateItem 和 Evidence 聚合为同一个现实 AI 事件的当前可审核判断。聚类算法与状态判定算法不属于本节点。

### 字段语义

| 字段 | 必须 | 语义与边界 |
| --- | --- | --- |
| `event_id` | Yes | 唯一且稳定的事件标识。 |
| `canonical_title` | Yes | 事件标准标题；不得夸大证据所支持的范围。 |
| `region` | Yes | `Global` 或 `China`；与所属日报链一致。 |
| `technical_categories` | Yes | 使用本文件冻结的技术分类，允许多选。 |
| `first_seen_at` | Yes | 系统首次发现该事件的时间。 |
| `last_seen_at` | Yes | 最近一个相关候选项或证据被观察到的时间。 |
| `evidence_references` | Yes | 当前用于支持、反驳或补充该事件的 Evidence 集合。 |
| `information_status` | Yes | 只使用 Stage 1.1 的四类信息状态。 |
| `current_confidence` | Yes | 事件级当前可信度；可表达为 `High`、`Medium` 或 `Low`，具体计算未在本节点定义。 |
| `importance` | Yes | 事件对日报的相对重要度；可表达为 `Critical`、`High`、`Medium` 或 `Low`，排序算法未定义。 |
| `why_it_matters` | Yes | 说明该事件对 AI 行业、用户或 Eterna 研究的意义，不代替原始证据。 |
| `eterna_tags` | Yes | 使用本文件冻结的 Eterna 标签集合。 |
| `status_history` | Yes | 追加式记录每次状态变更的时间、旧状态、新状态、依据证据与理由。 |

### 事件更新边界

- 同一事件允许随新证据更新 `information_status`、`current_confidence`、`importance` 与 `why_it_matters`。
- 每次信息状态变更必须追加 `status_history`，不得覆盖之前的状态、理由或当时证据。
- Evidence 集合可追加、标记冲突或变为不可访问，但不得伪造、静默删除或改写历史来源。

---

## IntelligenceReport

### 职责

IntelligenceReport 是 Global 或 China 独立日报的最终数据对象，组织已选事件、核心摘要、重要性顺序、Eterna 价值提取和来源覆盖情况。

### 字段语义

| 字段 | 必须 | 语义与边界 |
| --- | --- | --- |
| `report_id` | Yes | 唯一标识该日报。 |
| `region` | Yes | `Global` 或 `China`；两类报告独立生成。 |
| `report_date` | Yes | 报告所属业务日期，必须与明确时区共同解释。 |
| `coverage_started_at` | Yes | 本报告覆盖时间窗口开始。 |
| `coverage_ended_at` | Yes | 本报告覆盖时间窗口结束。 |
| `event_references` | Yes | 按明确顺序引用本报告包含的 IntelligenceEvent 列表。 |
| `core_summary` | Yes | 对报告时间窗口的核心摘要，不得覆盖事件或证据引用。 |
| `importance_order` | Yes | 记录重要事件的输出顺序及可审核理由；排序逻辑未在本节点实现。 |
| `eterna_value_extraction` | Yes | 使用 Stage 1.1 的“直接有用 / 值得跟踪 / 暂无行动价值”评估 Eterna 关联，不自动修改 Eterna 路线。 |
| `report_generated_at` | Yes | 报告对象完成生成的时间。 |
| `source_coverage_statistics` | Yes | 统计来源类型、P0–P3、已观测/不可用数量和时间窗口；不伪造覆盖率。 |

IntelligenceReport 只引用与本报告 `region` 一致的 IntelligenceEvent。

---

## 分类字段

### 技术分类

`technical_categories` 至少支持：

- `Model`
- `Agent`
- `AI Coding`
- `Voice / STS`
- `Multimodal`
- `Robotics / Embodied AI`
- `Open Source`
- `Infrastructure`
- `Research`
- `Product`
- `Business / Ecosystem`

同一候选项或事件可使用多个技术分类，但不得用分类代替事实状态。

### Eterna 标签

`eterna_tags` 至少支持：

- `Digital Resident`
- `Aftelle`
- `Studio Next`
- `Runtime Core`
- `ECCS`
- `Voice / STS`
- `Multimodal`
- `Agent`
- `AI Coding`
- `Business / Ecosystem`

Eterna 标签只表示研究关联，不构成产品路线、实施优先级或 `FROZEN` 文档变更。

---

## 时间规范

| 时间字段 | 定义 | 禁止替代 |
| --- | --- | --- |
| `source_published_at` | 原始来源明确标注的发布时间。 | 不得用 `collected_at`、`first_seen_at` 或搜索引擎时间推测。 |
| `collected_at` | Collector 合法获得条目或元数据的时间。 | 不得写作来源发布时间。 |
| `first_seen_at` | 系统首次观察到候选项或事件的时间。 | 不得自动等同于 `source_published_at`。 |
| `last_seen_at` | 系统最近一次观察到候选项或事件更新的时间。 | 不得用于覆盖首次发现或发布时间。 |
| `report_generated_at` | IntelligenceReport 完成生成的时间。 | 不得代替报告覆盖窗口或事件时间。 |

统一要求：

- 时间表达必须使用包含时区偏移的明确标准时间，或使用明确的 UTC `Z` 时间。
- 日报 `report_date` 必须与明确的报告时区绑定。
- 来源未提供发布时间时，`source_published_at` 保留为未知，不用其他时间猜测。
- 展示层可转换时区，但不得丢失原始时区信息或标准化时间。

---

## 信息状态边界

IntelligenceEvent 的 `information_status` 只沿用 Stage 1.1 已冻结的四类状态：

| 状态 | 语义 |
| --- | --- |
| `Confirmed` | 已由官方、一手公开材料或其他可核验证据确认。 |
| `High-confidence signal` | 有可信公开来源或多项独立证据支持，但尚未完成官方确认。 |
| `Unconfirmed` | 具有记录价值，但证据不足、无法独立核验或仍属传闻。 |
| `Community trend` | 公开社区中重复出现的讨论、使用体验、实测或趋势信号，不等同于已确认事实。 |

不得新增含义冲突的事件状态。以下概念必须区分：

| 概念 | 层级 | 含义 |
| --- | --- | --- |
| `source_priority` | Source / CandidateItem / Evidence | 来源的默认监控优先级。 |
| `source_credibility` | Source / CandidateItem / Evidence | 来源级可信度。 |
| `current_confidence` | IntelligenceEvent | 基于当前 Evidence 集合的事件级可信度。 |
| `information_status` | IntelligenceEvent | Stage 1.1 冻结的事件信息状态。 |

高优先级或高可信来源不会自动将事件标记为 `Confirmed`；P3 来源也不会因讨论量高而自动变为官方事实。

---

## 可追溯性要求

```text
IntelligenceReport.event_references
→ IntelligenceEvent.evidence_references
→ Evidence.candidate_references
→ CandidateItem.source_reference + source_url + raw_evidence_reference
→ Source Registry + 原始公开来源
```

必须保证：

- 从 IntelligenceReport 中的任一 Event 可反向追踪至 Evidence、CandidateItem、Source Registry 和原始公开 URL。
- CandidateItem、Evidence、IntelligenceEvent 和 IntelligenceReport 的关联通过显式引用保留，不依赖摘要文本猜测来源。
- 任何 AI 摘要、状态判断、`why_it_matters` 或 Eterna 价值分析都不得覆盖、删除或改写原始证据。
- 原始来源后续不可访问时，只能保留已合法取得的最小必要公开信息、原始 URL、时间与不可访问状态，不得伪造正文。
- 事件状态更新通过追加式 `status_history` 保留历史，不得覆盖当时证据与判断。

---

## Global / China 边界

- 每个 CandidateItem 必须带 `region = Global` 或 `region = China`。
- Evidence 保留所引 CandidateItem 的 Region 链路。
- IntelligenceEvent 必须属于单一 Region，不在本节点建立跨区混合 Event。
- Global 与 China IntelligenceReport 独立生成，各自使用本 Region 的 Event 列表、摘要与来源覆盖统计。
- 跨区域同一现实事件可在后续节点研究关联，但不得在 Stage 1.4 破坏两条独立日报链，也不在本节点设计跨区聚类算法。

---

## 合规与隐私边界

以下规则为硬约束：

- 数据模型不得定义或保存 Cookie、Session、Token、API Key、账号密码或其他认证凭证字段。
- 不保存绕过登录、验证码、付费墙、Rate Limit、访问控制或平台安全机制所得数据。
- 搜索摘要、社区信息、人物观点或媒体转述不得自动提升为官方事实。
- 原始来源不可访问时不得伪造标题、摘要、正文、发布时间或证据。
- 只保存完成情报分析所需的最小必要公开信息和来源引用，不收集与情报目的无关的个人数据。
- 任何对象中的 AI 生成内容都必须与原始公开证据分开保留。

---

## Stage 1.4 明确不做

- 不实现 Python、TypeScript、Swift 或其他业务代码。
- 不实现 JSON Schema、Pydantic Model、SQL Schema 或编程语言类。
- 不进行数据库选型。
- 不创建数据库、表、索引或迁移。
- 不实现 Collector。
- 不设计或实现去重算法。
- 不设计或实现事件聚类算法。
- 不编写 LLM Prompt。
- 不实现 AI 摘要逻辑。
- 不实现 Gmail 发送。
- 不创建 GitHub Actions。
- 不创建定时任务或其他自动执行。
- 不定义或开始 Stage 1.5 内容。

本节点只冻结概念数据契约与字段语义。

---

## Stage 1.4 节点验收标准

Stage 1.4 仅在以下条件全部满足时通过：

- CandidateItem、Evidence、IntelligenceEvent 与 IntelligenceReport 四层对象的职责和边界已定义。
- 来源、时间、信息状态、技术分类、Eterna 标签和追溯字段完整。
- CandidateItem → Evidence → IntelligenceEvent → IntelligenceReport 可反向追踪到原始公开来源。
- Global / China 独立日报边界保持，未设计跨区聚类算法。
- 概念契约与 Stage 1.1–1.3 无冲突。
- 本文件未定义敏感凭证字段，也未存储任何敏感凭证值。
- 本节点未进入代码、Schema、数据库、Collector、去重、聚类或分析实现。
- 本节点未修改 Stage 1.1–1.3 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.5。
