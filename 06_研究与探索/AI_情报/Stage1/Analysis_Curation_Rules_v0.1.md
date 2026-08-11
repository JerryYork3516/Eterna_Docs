# AI 情报自动化系统 · Analysis and Curation Rules · Stage 1.6 · v0.1

内部版本：`v0.1`

文档性质：AI 情报分析、筛选与摘要规则

状态：`FROZEN`

文档更新时间：`2026-08-11 20:28`（Asia/Shanghai）

> 本文件冻结 AI 情报系统 Stage 1.6 的日报准入、可信度、信息状态、重要性、排序与事实约束摘要规则。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、LLM Prompt、评分算法、代码实现或真实日报。

---

## 文档地位与边界

- 本文件承接 Stage 1.1 的范围与信息状态、Stage 1.2 Source Registry、Stage 1.3 Collection Architecture、Stage 1.4 Intelligence Data Model 和 Stage 1.5 Dedup and Clustering Rules。
- 本节点只冻结分析规则与输出语义，不修改 Stage 1.1–1.5 或任何 Eterna `FROZEN` 上位文档。
- 本节点不实现 LLM Prompt，不调用模型，不实现评分代码，不创建数据库，也不生成真实日报。
- 本节点不设计 Eterna 价值评分、行动建议或路线调整逻辑，也不开始 Stage 1.7。

---

## 分析处理关系

```text
IntelligenceEvent
↓
Eligibility Filter
↓
Confidence Assessment
↓
Importance Assessment
↓
Summary / Why it matters
↓
Daily Report Candidate
```

- Eligibility Filter 只判断 Event 是否适合进入本次日报，不修改或删除原始 Evidence。
- Confidence、Status 与 Importance 是不同维度，必须分别判断和展示。
- 摘要只压缩已有 Evidence，不替代 IntelligenceEvent、Evidence 或原始来源。
- `why_it_matters` 只解释日报关注价值，不参与事实确认。
- Eterna 相关性和后续价值分析不得参与事实、可信度或信息状态判断。
- Daily Report Candidate 是进入报告编排的候选输出，不表示本节点已生成真实日报。

---

## 日报准入规则

IntelligenceEvent 进入本次日报时，至少核对：

- 时间窗口：本次报告覆盖窗口内出现新 Event，或既有 Event 出现新增 Evidence 或重大更新。
- 可追溯性：核心陈述能够通过 Evidence、CandidateItem、Source Registry 追溯至原始公开 URL。
- 信息范围：事件属于 Stage 1.1 允许纳入的 AI 模型、产品、API、研究、人物、社区、媒体或行业信息范围。
- 信息增量：相较既有记录或上次日报，存在新的事实、信号、冲突、状态变化或有意义的趋势变化。
- 关注价值：事件具有技术、产品、开发者、用户、研究、市场、商业、监管或生态价值，或具有明确的社区趋势发现价值。
- 合规性：现有 Evidence 均来自公开、合法、获得授权或目标平台明确允许的访问方式。
- 噪声控制：事件不只是低价值重复转载、营销噪声或无新增信息的讨论。

所有条件必须结合 Event 的 Evidence 实际判断，不以热度、来源数量或 Eterna 相关度替代准入依据。

### 既有 Event 再次准入

同一 Event 已在此前日报出现时，只有出现实质更新才应再次进入日报。实质更新至少可以包括：

- 新的一手来源确认或撤回核心事实。
- `information_status` 或 `current_confidence` 因新 Evidence 发生有依据的变化。
- 新增价格、可用地区、发布时间、版本、能力范围或 API 条件等关键事实。
- 新增重要 `Contradicts` Evidence、纠正或澄清。
- 出现能够改变事件影响判断的开发者、用户、市场、监管或社区反馈。

仅增加 Near Duplicate、转载数量、相似标题、讨论量或无新增内容的反馈，不构成实质更新。

---

## 低价值过滤规则

以下内容不得作为独立日报条目进入 Daily Report Candidate：

- 纯营销宣传，但没有新的可核验事实、产品变化或能力信息。
- 重复转载、同源传播或标题改写，且没有新增信息。
- 标题党、来源不可追溯或无法定位原始事件的内容。
- 与 AI 没有实质关系的泛科技内容。
- 单纯情绪表达、立场争论或无可复核内容的讨论。
- 无法确认主体、对象、行为或版本的模糊传闻。
- 没有实际新增信息的社区重复讨论。
- 只因热度高，但没有技术、产品、市场、生态、开发者或用户价值的信息。
- 搜索摘要不足以支持核心陈述，且无法合法取得可核验原始来源的内容。

过滤只影响本次日报准入，不删除 CandidateItem、Evidence、IntelligenceEvent、历史状态或追溯链。后续出现实质 Evidence 时，可以重新评估该 Event。

---

## current_confidence 判断规则

`current_confidence` 继续只使用 Stage 1.4 的三个等级：

- `High`
- `Medium`
- `Low`

### 与其他概念的区别

| 概念 | 层级 | 含义 |
| --- | --- | --- |
| `source_priority` | Source / CandidateItem / Evidence | 来源的默认监控优先级 `P0`–`P3`。 |
| `source_credibility` | Source / CandidateItem / Evidence | 来源级默认可信度，不是对当前事件的结论。 |
| `information_status` | IntelligenceEvent | `Confirmed`、`High-confidence signal`、`Unconfirmed` 或 `Community trend` 的事件状态。 |
| `current_confidence` | IntelligenceEvent | 当前 Evidence 集合对事件核心陈述的支持强度与不确定性判断。 |

四者不得混用。高优先级来源不自动产生高 Event Confidence，高 Confidence 也不自动等于 `Confirmed`。

### 判断依据

可信度判断至少考虑：

- 是否存在对核心事件事实具有自身权威的 P0 一手来源。
- 是否存在多个真正独立、可追溯且非同源传播的来源。
- `Supports` Evidence 是否在主体、对象、版本、时间和核心行为上相互支持。
- 是否存在 `Contradicts` Evidence，以及冲突是否影响核心事实。
- 是否存在版本、时间、主体、对象或事件身份歧义。
- 来源是否只是转载、聚合、引用同一基础材料或近重复传播。
- 是否只有搜索摘要、单一人物信号或社区线索。
- 来源的 Fact Citation 边界是否覆盖当前陈述。

### 等级边界

| 等级 | 语义边界 |
| --- | --- |
| `High` | 核心陈述由权威范围内的一手来源或充分独立、可核验且一致的 Evidence 支持，没有未解释的重大反证或关键身份歧义。 |
| `Medium` | Evidence 具有实际支持价值，但仍存在有限缺口、间接性、待确认细节或不影响核心身份的冲突。 |
| `Low` | Evidence 单一、间接、同源、只含搜索摘要或社区线索，或存在关键缺口、重大歧义、未解决反证。 |

硬规则：

- 来源数量不能简单等同于可信度。
- 10 个转载同一来源不能视为 10 个独立 Evidence。
- P0 来源只在其自身权威范围内作为一手事实；官方 benchmark 宣称不自动证明客观领先。
- 存在明确反证时不得忽略、隐藏或仅凭来源等级压低其可见性。
- 本节点不定义数学公式、评分权重、数值阈值或自动判定算法。

---

## information_status 判定边界

`information_status` 继续只允许 Stage 1.1 / 1.4 已冻结的四类状态：

| 状态 | 判定边界 |
| --- | --- |
| `Confirmed` | 存在足以确认核心事件事实的一手公开材料或其他可核验证据；确认范围不得超出来源自身权威和 Evidence 支持范围。 |
| `High-confidence signal` | Evidence 较强、可追溯且具有实际支持，但核心事实尚未达到 `Confirmed`。 |
| `Unconfirmed` | Evidence 不足、来源单一、存在关键缺口、重大歧义或无法独立核验。 |
| `Community trend` | 核心价值是可观察的用户讨论、使用反馈、产品传播或社区趋势，而不是官方事件事实。 |

禁止：

- 因讨论量高自动升级状态。
- 因媒体或转载数量多自动升级状态。
- 因人物身份、影响力或职位高自动升级状态。
- 因与 Eterna 高相关自动升级状态。
- 因 `current_confidence = High` 而省略独立的状态判定。

状态变化继续遵守 Stage 1.4 / 1.5：必须追加 `status_history`，记录触发变化的 Evidence 与理由，不覆盖旧状态和历史来源。

---

## importance 重要性等级

`importance` 继续只使用 Stage 1.4 的四个等级：

- `Critical`
- `High`
- `Medium`
- `Low`

### 判断维度

重要性至少考虑：

- 是否为重大模型、产品、API、研究或平台首发。
- 是否改变可用技术能力或行业能力边界。
- 是否显著影响 API、价格、模型能力、开发工具或基础设施。
- 是否影响大量开发者、用户或重要使用场景。
- 是否为具有广泛后续影响的重要研究突破。
- 是否属于重大商业、竞争、监管、融资或生态变化。
- 是否只是小版本、小功能、局部营销事件或有限范围调整。

### 等级边界

| 等级 | 语义边界 |
| --- | --- |
| `Critical` | 可能显著改变行业能力边界、主要平台格局、广泛开发者/用户条件或重大监管与生态环境。 |
| `High` | 对重要模型、产品、研究、开发工具、基础设施或市场产生明显且较广影响。 |
| `Medium` | 具有明确新增价值和关注必要性，但影响范围、变化程度或受众相对有限。 |
| `Low` | 小版本、小功能、局部调整或有限营销事件；只有存在实际信息增量时才可能进入日报。 |

重要性与可信度完全独立，例如：

- 高重要性传闻可以是 `Critical + Low confidence`。
- 已确认的小功能更新可以是 `Low + High confidence`。

重要性高不得掩盖不确定性，可信度高也不得自动提高重要性。

---

## 日报排序原则

在同一 Region 日报内，默认依次考虑：

1. Importance。
2. Information Status。
3. Confidence。
4. 新鲜度。
5. 信息增量。
6. 来源质量。

该顺序表示排序判断维度，不冻结数值权重、评分公式、阈值或具体算法。`Community trend` 是独立状态类型，不因其不是官方事实而自动排到所有事件之后；其位置仍由重要性和实际趋势价值共同约束。

排序必须避免：

- 单纯按热度、浏览量或讨论量排序。
- 单纯按来源、媒体或转载数量排序。
- 单纯按 Eterna 相关度、标签数量或潜在行动价值排序。
- 为提高排名而提升 `information_status`、`current_confidence` 或 `importance`。

---

## Event 摘要规则

每个 Daily Report Candidate 至少输出：

| 输出项 | 语义 |
| --- | --- |
| `What happened` | 基于 Evidence 描述发生了什么、主体、对象、版本、时间与本次实质更新。 |
| `Status` | 展示 Event 的 `information_status`。 |
| `Confidence` | 展示 Event 的 `current_confidence`。 |
| `Evidence / Sources` | 展示主要一手来源、必要补充来源、冲突情况与原始 URL。 |
| `Why it matters` | 解释该事件为什么值得 AI 情报日报关注。 |

摘要必须：

- 只依据当前 Event 已关联的合法 Evidence。
- 不加入来源没有支持的事实、数字、版本、时间或因果关系。
- 明确区分来源事实、来源宣称、社区反馈和分析推断。
- 保留关键模型名、版本号、时间、公司、产品和 API 名称。
- 对不确定信息明确写明“不确定”或“未确认”。
- 对存在 `Contradicts` Evidence 的核心内容明确说明冲突和当前未决边界。
- 保留反向追溯到原始 URL 的能力。
- 将本次新增内容与已知历史背景分开，不把旧闻改写为新事件。

摘要禁止：

- 幻觉补全或依赖模型常识补写 Evidence 中缺失的事实。
- 把推断、预测、观点或营销宣称写成事实。
- 把媒体标题改写成比原文更强的结论。
- 把未来计划、预告、路线图或测试阶段写成已发布或已上线。
- 把官方或媒体的 benchmark 宣称直接写成客观领先结论。
- 用摘要替代、删除或覆盖原始 Evidence 与来源。

本节只冻结输出语义，不构成 LLM Prompt、模板实现或真实日报内容。

---

## Why it matters 边界

`why_it_matters` 只回答：“为什么这件事值得 AI 情报日报关注？”

可以涉及：

- 技术能力变化。
- 产品与可用性变化。
- 开发者工具、成本或工作流影响。
- 用户体验、采用或风险影响。
- 市场、商业与竞争影响。
- 生态、基础设施或监管影响。

`why_it_matters` 不得：

- 替代 `What happened` 的事实摘要。
- 增加 Evidence 未支持的事实或因果关系。
- 自动升级 `information_status`、`current_confidence` 或 `importance`。
- 自动改变 Eterna 路线、产品定义或任何 `FROZEN` 文档。
- 在 Stage 1.6 输出 Eterna 行动建议或价值评分。

---

## 来源展示规则

日报中每个 Event 至少能够展示：

- 主要一手来源及其原始 URL；若不存在，必须明确说明。
- 支撑核心陈述所必要的补充来源及原始 URL。
- 是否存在 `Contradicts` Evidence，并展示必要的冲突来源。
- 来源的事实引用边界，以及只包含搜索摘要或社区线索等限制。

正文不需要堆叠全部 Near Duplicate 或转载，但底层必须保留完整的 IntelligenceEvent → Evidence → CandidateItem → Source Registry → 原始 URL 追溯链。隐藏近重复展示不得变成删除来源记录。

---

## Global / China 边界

- Global IntelligenceEvent 只进入 Global Report 的筛选、排序和摘要流程。
- China IntelligenceEvent 只进入 China Report 的筛选、排序和摘要流程。
- 两份日报独立判断准入、Confidence、Status、Importance、排序与摘要。
- Stage 1.6 不跨 Region 合并 Event，不统一排序，也不生成混合摘要。

---

## Eterna 价值分析边界

Stage 1.6 只确认分析输出应支持后续 Stage 1.7 读取：

- `technical_categories`
- `eterna_tags`
- `why_it_matters`
- `importance`
- `current_confidence`
- `evidence_references`

这些字段只构成后续输入接口语义。本节点不设计 Eterna 价值评分、行动建议、优先级计算或路线调整逻辑。

Eterna 标签、相关性或潜在价值不得参与事实确认、Confidence、Information Status 或现实事件身份判断。

---

## 合规边界

以下规则为硬约束：

- 不因分析、核验或摘要需要重新抓取受限内容。
- 不绕过登录、验证码、Rate Limit、付费墙、访问控制或其他安全机制。
- 不调用、逆向或伪造未授权私有 API。
- 不保存 Cookie、Session、Token、API Key、密码或其他认证凭证。
- 不让模型或人工流程补造不可访问的来源正文、缺失上下文或不存在的证据。
- 只依据公开、合法、获得授权或目标平台明确允许取得的信息生成判断。
- 不因信息不足、事件重要或 Eterna 相关度高而降低事实标准。

---

## Stage 1.6 明确不做

- 不编写 LLM Prompt。
- 不调用 OpenAI、Gemini、Claude 或其他模型。
- 不实现 Python、TypeScript、Swift 或其他业务代码。
- 不定义或实现评分公式、数值权重或阈值。
- 不使用或选择 embedding 模型。
- 不创建向量数据库或向量检索。
- 不实现数据库、JSON Schema、Pydantic Model 或 SQL Schema。
- 不生成真实日报或实际 Daily Report Candidate。
- 不设计 Eterna 价值评分、行动建议或路线调整逻辑。
- 不实现 Gmail 发送。
- 不创建 GitHub Actions。
- 不创建自动化或定时任务。
- 不定义或开始 Stage 1.7 内容。

本节点只冻结分析规则与输出语义。

---

## Stage 1.6 节点验收标准

Stage 1.6 仅在以下条件全部满足时通过：

- 日报准入、既有 Event 再次准入与低价值过滤规则明确。
- `current_confidence`、`information_status` 与 `importance` 的等级、依据和相互边界明确。
- 日报排序原则明确，且未冻结评分公式、数值权重、阈值或算法。
- `What happened`、`Status`、`Confidence`、`Evidence / Sources` 与 `Why it matters` 输出语义明确。
- 摘要只依据 Evidence，能够展示不确定性、冲突与原始来源。
- Global / China 独立筛选、排序和摘要，未跨 Region 合并或统一排序。
- Eterna 相关性未用于事实、可信度、信息状态或事件身份判断。
- 本节点未进入 LLM Prompt、模型调用、算法、代码、Schema、数据库或真实日报实现。
- 本节点未修改 Stage 1.1–1.5 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.7。
