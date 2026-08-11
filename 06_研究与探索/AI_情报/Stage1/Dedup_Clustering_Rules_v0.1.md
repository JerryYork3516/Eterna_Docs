# AI 情报自动化系统 · Dedup and Clustering Rules · Stage 1.5 · v0.1

内部版本：`v0.1`

文档性质：AI 情报去重与事件聚类规则

状态：`FROZEN`

文档更新时间：`2026-08-11 19:50`（Asia/Shanghai）

> 本文件冻结 AI 情报系统 Stage 1.5 的 CandidateItem 去重、Evidence 形成与 IntelligenceEvent 聚类规则。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、算法实现、Schema、数据库设计或模型方案。

---

## 文档地位与边界

- 本文件承接 Stage 1.1 的信息状态与合规边界、Stage 1.2 Source Registry、Stage 1.3 Collection Architecture 和 Stage 1.4 Intelligence Data Model。
- 本节点只冻结规则、语义与判定边界，不修改 Stage 1.1–1.4 或任何 Eterna `FROZEN` 上位文档。
- 本节点不实现算法代码，不调用 LLM，不创建数据库，不实现 embedding、向量检索或相似度阈值。
- 本节点不改变 Eterna 正式定义，也不开始 Stage 1.6。

---

## 处理关系

```text
CandidateItem observations
↓ Exact Duplicate 折叠
CandidateItem set
↓ Near Duplicate / Same Event 关系判断
Evidence
↓ 现实事件身份判断
IntelligenceEvent
```

- 去重处理的是重复观察或高度相似内容，不得删除独立来源的证据价值。
- 事件聚类处理的是现实事件身份，不以标题、关键词、技术分类或 Eterna 相关性代替身份判断。
- CandidateItem 不是事实；形成 Evidence 或进入 IntelligenceEvent 后仍须沿用 Stage 1.4 的来源、状态与追溯边界。

---

## 去重层级

### Exact Duplicate

Exact Duplicate 指同一来源对象或同一公开内容被重复观察，未产生新的独立内容或证据。

典型情况：

- 同一 canonical URL 被重复采集。
- 同一官方 API object ID 被重复返回。
- 同一 Feed item、GUID 或等价来源对象重复出现。
- 同一来源对象只因采集批次不同而再次进入系统。

处理规则：

- 只保留一个主 CandidateItem，其他重复观察不得生成重复日报条目。
- 必须保留首次发现时间、最近发现时间，以及重复观察次数或等价的可追溯记录能力。
- 重复观察可更新可用性和最近发现时间，但不得覆盖原始 URL、首次发现时间或历史观察。
- 若同一 URL 或 object ID 的公开内容发生实质变化，不得仅因标识相同而静默覆盖；应保留变化观察，并重新判断其属于补充 Evidence 还是新的 Event。

### Near Duplicate

Near Duplicate 指内容表达基本相同，但来源、URL、标题、平台或载体不同。

典型情况：

- 官方 Blog 与官方 X 发布同一公告。
- 不同媒体转载或概述同一官方内容。
- 同一模型发布在多个平台被重复转发或改写标题。

处理规则：

- 不得把 Near Duplicate 当作 Exact Duplicate 直接删除。
- 每个独立来源保留自己的 CandidateItem、原始 URL、来源属性和发布时间。
- 内容高度重合的来源可标记为近重复关系，但不得把转载数量误认为多项独立事实确认。
- Near Duplicate 可分别形成 Evidence；Evidence 的一手性、来源等级和支持关系必须独立保留。
- 日报可以合并叙述同一事件，但不得丢失独立来源引用。

### Same Event, Different Evidence

Same Event, Different Evidence 指不同内容从不同角度描述同一个现实事件，内容不应被作为重复删除。

典型情况：

- 官方宣布模型发布。
- 核心人物补充能力范围或上线说明。
- 媒体报道同次发布中的价格信息。
- Reddit 用户提供该次发布后的公开实测反馈。

处理规则：

- 各 CandidateItem 保持独立，并按 `Supports`、`Contradicts` 或 `Supplements` 形成 Evidence。
- 若现实事件身份一致，这些 Evidence 进入同一个 IntelligenceEvent。
- 来源数量、转发数量或讨论热度不得自动提高事件状态或可信度。
- Same Event 关系表示事件身份相同，不表示各来源内容相互独立、完全一致或均可作为事实引用。

---

## 去重判断信号

以下信号用于形成可审核判断，不规定算法、权重、阈值或实现方式：

| 判断信号 | 用途 | 边界 |
| --- | --- | --- |
| canonical URL | 识别 URL 规范化后是否指向同一公开对象。 | 相同 URL 的内容可能更新，不能自动覆盖历史。 |
| source URL | 保留来源入口并发现重复访问。 | 参数、短链或镜像差异不等于独立证据。 |
| source object ID | 识别 API、Feed、Release 或平台对象身份。 | 只在来源自身对象空间内解释。 |
| 标题相似性 | 发现可能的重复或同事件候选。 | 不能单独决定删除或聚类。 |
| 正文/摘要相似性 | 判断内容是否近重复或来自同一基础材料。 | 搜索摘要不完整时不得补造上下文。 |
| 发布主体 | 判断组织、产品团队或个人是否一致。 | 同一主体可同时发生多个事件。 |
| 模型/产品名称 | 识别事件对象。 | 产品家族名称相同不表示具体产品或版本相同。 |
| 版本号 | 区分同一产品的不同发布。 | 明确不同版本时禁止自动合并。 |
| 时间接近度 | 判断描述是否可能属于同一事件窗口。 | 时间接近不是充分条件，合理窗口不在本节点量化。 |
| 关键实体 | 对齐公司、人物、模型、产品、API 或研究项目。 | 只共享部分实体不能证明事件相同。 |
| Event 类型 | 区分发布、上线、调价、能力更新、研究公开等现实行为。 | 不定义分类算法或封闭枚举。 |

任何单一信号都不足以完成 Near Duplicate 或 Same Event 判断；多个信号一致也必须遵守误聚类保护原则。

---

## Evidence 形成规则

- Exact Duplicate 的重复观察关联至同一主 CandidateItem，不为同一来源对象重复制造相同 Evidence。
- Near Duplicate 的独立来源保留各自 CandidateItem，并分别形成可追溯 Evidence。
- Same Event, Different Evidence 的 CandidateItem 依据内容与事件关系标记为 `Supports`、`Contradicts` 或 `Supplements`。
- 转载、聚合或媒体改写必须保留其来源属性；能够回溯官方原文时，同时保留官方来源与转述来源之间的关系。
- 搜索摘要或元数据不足以支持正文结论时，只能形成受限 Evidence，不得推断缺失内容。
- Evidence 是否一手、来源 Priority、来源 Credibility 和 Fact Citation 边界继续沿用 Stage 1.2 / 1.4，不因聚类自动改变。

---

## IntelligenceEvent 聚类规则

多个 CandidateItem 只有在实际描述同一个现实事件时，才允许进入同一个 IntelligenceEvent。

### 身份判断条件

聚类判断至少核对：

- 主体一致：实施或宣布行为的组织、团队或人物能够对齐。
- 行为一致：发布、上线、调价、能力更新、研究公开等核心行为能够对齐。
- 对象一致：模型、产品、API、研究或公司动作指向同一对象。
- 版本一致：存在版本时指向同一版本或明确属于同次发布。
- 时间窗口合理：发布时间、发生时间和补充说明处于可解释的同一事件窗口。
- 核心事实不存在事件身份层面的明显冲突。

必要身份信息缺失或互相矛盾时，不得自动合并。属性层面的冲突不一定改变事件身份，应按“冲突 Evidence 规则”处理。

### 应聚类示例

以下内容可在身份条件满足时进入同一 Event：

- “OpenAI 发布某模型”。
- “OpenAI 官方 X 宣布该模型上线”。
- “Tibo 说明该模型同次发布中的某项能力”。

### 不应聚类示例

- “Gemini 4 发布”。
- “Gemini App 更新 UI”。

即使两项内容发布时间接近、主体相关或共享 `Gemini` 关键词，核心行为与对象仍不同，必须建立不同 Event。

---

## 冲突 Evidence 规则

当来源针对同一个现实事件产生冲突时：

- 不得删除较弱来源。
- 不得只保留官方结论而隐藏历史冲突。
- 不得为了规避矛盾而强行拆分已确认属于同一现实事件的内容。
- 必须进入同一个 IntelligenceEvent，并建立 `Contradicts` Evidence。
- 必须保留双方 CandidateItem、原始 URL、来源等级、发布时间与获取时间。
- 后续由信息状态与可信度判定处理冲突，本节点不定义计算公式。

若冲突实际涉及不同主体、不同版本、不同产品或不同核心行为，则属于事件身份不一致，不适用“同一 Event 内冲突”的前提，应按保守原则分开。

---

## Event 身份与更新边界

### 保持原 event_id

下列变化不改变现实事件身份时，必须保持原 `event_id`：

- 新增支持、反驳或补充 Evidence。
- 官方确认此前针对同一事件的传闻或高可信消息。
- 补充同次事件的价格、发布时间、地区或能力范围。
- 社区新增针对同一发布或同一事件的公开实测反馈。
- canonical title 因信息更准确而调整。

不得仅因标题、摘要措辞、来源数量或信息状态变化创建新 Event。

### 建立新 Event

下列情况应建立新的 `event_id`：

- 新版本发布。
- 独立产品、模型、API 或研究成果发布。
- 原事件之后发生新的重大动作，例如独立调价、下架、重大版本更新或政策变化。
- 事件主体改变。
- 核心行为改变，已无法解释为原事件的补充或状态更新。

同一产品的长期演进可以包含多个 Event，不得用单一 Event 无限吸收后续独立动作。

---

## 信息状态演进

IntelligenceEvent 继续只使用 Stage 1.1 / 1.4 的状态：

- `Unconfirmed`
- `High-confidence signal`
- `Confirmed`
- `Community trend`

典型演进可以是：

```text
Unconfirmed
→ High-confidence signal
→ Confirmed
```

规则：

- 状态可随新增 Evidence、官方确认、来源撤回或反证发生变化。
- 每次变化必须追加 `status_history`，记录旧状态、新状态、时间、触发 Evidence 与理由。
- 不得覆盖旧状态、当时依据或历史来源。
- `Community trend` 表示社区趋势类型，不是必然通向 `Confirmed` 的低级状态；只有同一现实事件获得足够新证据时才可调整。
- 讨论量、Near Duplicate 数量或转发数量不能单独触发状态提升。
- 本节点不设计置信度计算公式、评分权重或状态转换阈值。

---

## Global / China 边界

- Global CandidateItem 只形成 Global Evidence 并进入 Global IntelligenceEvent。
- China CandidateItem 只形成 China Evidence 并进入 China IntelligenceEvent。
- Stage 1.5 不建立跨 Region Event，也不执行跨区域合并。
- 同一现实事件同时被国内外来源报道时，两条链可分别形成各自 Event，并分别保留来源与状态。
- 后续 Stage 可研究跨区域关联，但不得在本节点破坏两条独立日报链。

---

## Eterna 相关性排除规则

以下内容不得作为两个条目属于同一现实事件的主要依据：

- `eterna_tags`
- `why_it_matters`
- Eterna 价值提取或“直接有用 / 值得跟踪 / 暂无行动价值”判断

事件身份必须基于现实主体、行为、对象、版本、时间与证据。两个条目即使都与 Aftelle、Studio Next、Runtime Core、ECCS 或其他 Eterna 方向相关，也不能因此合并。

Eterna 相关性只能在事件身份确定后用于后续价值分析。

---

## 误聚类保护

采用 Conservative Principle：宁可暂时保留两个 Event，也不要在证据不足时错误合并。

以下情况禁止自动合并：

- 版本号不同。
- 产品或模型不同。
- 主体不同。
- 核心行为不同。
- 时间跨度明显不合理且缺乏连续事件证据。
- 只因为关键词相似。
- 只因为标题相似。
- 只因为属于同一技术分类。
- 只因为 Eterna 标签或价值判断相同。

保留为两个 Event 不表示事实冲突已经解决；后续获得足够身份依据时可建立关联或重新判断，但必须保留历史处理记录。

---

## 可追溯性

聚类后必须保持：

```text
IntelligenceEvent
→ Evidence
→ CandidateItem
→ Source Registry
→ 原始 URL
```

必须保证：

- 去重和聚类不得删除或改写原始来源记录。
- Near Duplicate 和 Same Event 的每个独立 CandidateItem 均可从 Event 反向追踪。
- Exact Duplicate 折叠后仍保留首次发现时间、最近发现时间，以及重复观察次数或等价记录能力。
- Event 状态变化可追踪到触发变化的 Evidence 与对应 CandidateItem。
- 原始来源后续不可访问时，只记录不可访问状态，不伪造或补写原文。

本节点只冻结上述语义，不定义具体计数字段、存储结构或 Schema。

---

## 合规边界

以下规则为硬约束：

- 不为去重、比对或聚类重新抓取受限内容。
- 不通过绕过登录、验证码、付费墙、Rate Limit、访问控制或安全机制补全文本。
- 不调用、逆向或伪造未授权私有 API。
- 不保存 Cookie、Session、Token、API Key、账号密码或其他认证凭证。
- 不因内容不足让模型或人工流程伪造缺失上下文。
- 只依据公开、合法、获得授权或目标平台明确允许取得的信息判断。
- 采集失败、证据不足或聚类困难不得触发降低安全边界的策略。

---

## Stage 1.5 明确不做

- 不实现 Python、TypeScript、Swift 或其他业务代码。
- 不实现去重算法。
- 不使用或选择 embedding 模型。
- 不创建向量数据库或向量检索。
- 不编写 LLM Prompt，不调用 LLM。
- 不实现聚类模型。
- 不定义相似度阈值。
- 不实现数据库、JSON Schema、Pydantic Model 或 SQL Schema。
- 不实际处理 CandidateItem。
- 不实现 Collector。
- 不实现 AI 摘要。
- 不实现 Gmail 发送。
- 不创建 GitHub Actions。
- 不创建定时任务或其他自动执行。
- 不定义或开始 Stage 1.6 内容。

本节点只冻结规则与判定边界。

---

## Stage 1.5 节点验收标准

Stage 1.5 仅在以下条件全部满足时通过：

- Exact Duplicate、Near Duplicate 与 Same Event, Different Evidence 三层语义明确。
- canonical URL、source URL、source object ID、内容、实体、版本、时间和 Event 类型等判断信号完整。
- Event 聚类条件、冲突 Evidence 规则和 Event 身份更新边界明确。
- 信息状态演进保留 `status_history` 与触发 Evidence，不覆盖历史。
- Global / China 隔离保持，未建立跨 Region Event。
- Eterna 标签、`why_it_matters` 与价值判断未污染事件身份判断。
- Conservative Principle 与禁止自动合并条件已冻结。
- 去重后仍保持 IntelligenceEvent → Evidence → CandidateItem → Source Registry → 原始 URL 的完整追溯。
- 本节点未进入算法、代码、Schema、Prompt、数据库或模型实现。
- 本节点未修改 Stage 1.1–1.4 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.6。
