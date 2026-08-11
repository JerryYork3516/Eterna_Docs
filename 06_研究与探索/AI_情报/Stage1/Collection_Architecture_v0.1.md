# AI 情报自动化系统 · Collection Architecture · Stage 1.3 · v0.1

内部版本：`v0.1`

文档性质：AI 情报采集层架构方案

状态：`FROZEN`

文档更新时间：`2026-08-11 10:17`（Asia/Shanghai）

> 本文件冻结 AI 情报系统 Stage 1.3 的采集层架构、Collector 类型、来源映射、降级顺序与成本原则。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、采集授权或代码实现。

---

## 文档地位与边界

- 本文件承接 Stage 1.1 的目标与合规边界，以 Stage 1.2 Source Registry 为来源权威输入。
- 本节点只设计采集层方案，不修改 Stage 1.1、Stage 1.2 或任何 Eterna `FROZEN` 上位文档。
- 本节点不写采集代码，不部署服务，不配置 API，不创建 GitHub Actions 或其他自动化任务。
- 本方案不改变 Eterna 正式定义，也不开始 Stage 1.4。

---

## 总体架构

```text
Source Registry
↓
Collector Layer
↓
Normalizer
↓
Candidate Item
↓
Analysis Pipeline
```

| 层级 | 职责 | 明确不做 |
| --- | --- | --- |
| `Source Registry` | 提供来源名称、类型、地区、URL、P0–P3、可信度、事实引用边界和 Eterna 标签。 | 不触发采集，不保存采集状态。 |
| `Collector Layer` | 按登记来源选择合法采集方式，取得公开内容或变化信号，保留原始 URL 与获取时间。 | 不做事实判定，不生成 Eterna 结论。 |
| `Normalizer` | 将 API、Feed、网页与搜索发现的不同形式统一为稳定候选字段，保留来源证据与区域分区。 | 不改写原意，不将传闻提升为事实。 |
| `Candidate Item` | 作为进入分析层的单条标准化候选信息，携带可追溯来源和注册属性。 | 不等同于已确认事实或最终日报条目。 |
| `Analysis Pipeline` | 后续负责去重、证据评估、信息状态、摘要和 Eterna 价值提取。 | Stage 1.3 不设计或实现该层内部逻辑。 |

### Global / China 独立边界

- `Region = Global` 与 `Region = China` 从 Source Registry 到 Candidate Item 全程保持独立分区。
- Collector 不得将 Global 与 China 数据混成单一任务或摘要。
- 跨区重复内容只能在后续 Analysis Pipeline 按明确规则处理。

### Candidate Item 概念字段

Candidate Item 至少携带：

- 来源名称、类型、地区与优先级。
- Collector 类型与公开原始 URL。
- 原始标题或可识别摘要。
- 发布时间（若来源提供）与获取时间。
- 来源事实引用边界与 Eterna 关联标签。
- 原始证据引用或可复核的变化线索。

本节只定义概念契约，不冻结数据库 Schema、JSON Schema、类名或存储格式。

---

## Collector 选择原则

1. 只从 Source Registry 中已登记且未禁用的来源选择采集方式。
2. 优先使用来源方官方支持、公开且成本最低的方式。
3. 同一来源可登记主采集方式与合法备选方式，但不得设置绕过安全机制的备选。
4. P0 优先保证可追溯性；P1 优先保留信号上下文；P2 / P3 优先用于发现，不直接生成事实。
5. Global 与 China 使用独立来源集合和采集任务边界。

---

## Official API Collector

### 适用来源

- GitHub。
- Hugging Face。
- YouTube。
- X（仅在未来获得官方、合法接入条件时）。
- 其他明确提供开放接口的官方来源。

| 评估项 | 结论 |
| --- | --- |
| 数据类型 | Release、Commit、Issue、Repository 元数据、模型/数据集元数据、视频元数据、公开动态。 |
| 优势 | 结构化、时间戳稳定、可增量获取、原始对象可追溯。 |
| 限制 | 存在配额、Rate Limit、权限、产品条款和字段变更；部分平台需要授权。 |
| 成本 | 默认追求免费配额和最低请求量；额外付费或高配额需单独批准。 |
| Stage 1 推荐 | `Conditional Yes`：GitHub、Hugging Face 和 YouTube 可作为优先候选；X 不得成为 Stage 1 强依赖。 |

Official API Collector 的推荐不等于本节点已申请、配置或调用 API。

---

## RSS / Feed Collector

### 适用来源

- 官方 Blog 与 Newsroom。
- arXiv。
- Hacker News。
- 提供公开 Feed 的媒体网站。

| 评估项 | 结论 |
| --- | --- |
| 数据类型 | RSS / Atom 条目、标题、链接、时间、摘要和频道元数据。 |
| 优势 | 开放、轻量、低成本、易于增量处理，通常不需要账号。 |
| 限制 | 可能仅提供摘要、历史窗口有限、发布时间或 ID 不一致。 |
| 成本 | 低；优先使用免费原生 Feed。 |
| Stage 1 推荐 | `Yes`：作为有原生 RSS / Atom 来源的默认低成本方案。 |

### Feed 方案次序

1. 原生 RSS。
2. 原生 Atom Feed。
3. RSSHub 候选路由。

RSSHub 可作为候选方案，但不得默认依赖。只有在目标内容公开、路由使用合法、不绕过访问控制且经后续审核时，才能考虑使用。

---

## Web Page Monitor

### 适用来源

- 没有 RSS / Atom 的官方公开页面。
- 产品更新页面。
- Changelog、Release Notes 和官方公告列表。

| 评估项 | 结论 |
| --- | --- |
| 数据类型 | 页面标题、公开文本、时间、链接、页面版本或变化摘要。 |
| 发现方式 | 页面变化检测、公开 Sitemap 与合法 Search Discovery。 |
| 优势 | 覆盖没有 Feed 的 P0 官方发布与 Changelog。 |
| 限制 | 页面结构易变、动态渲染、变化噪声、时间字段不稳定。 |
| 成本 | 低至中；必须使用低频、最小页面范围和变化指纹。 |
| Stage 1 推荐 | `Conditional Yes`：仅用于无官方 API / Feed 的高价值公开页面。 |

Web Page Monitor 必须遵守页面访问条款、robots 约束与合理请求频率，不能将登录后页面或付费内容作为默认目标。

---

## Search Discovery Collector

### 适用来源

- TikTok。
- 抖音。
- 小红书。
- 微信公众号。
- 知乎。
- 其他只能通过合法搜索发现的社区趋势。

| 评估项 | 结论 |
| --- | --- |
| 数据类型 | 公开搜索结果、标题、摘要、原始链接与趋势线索。 |
| 优势 | 在不直接接入受限平台时发现新话题、用户反馈和社区趋势。 |
| 限制 | 覆盖不完整、排名不稳定、上下文有限，且受搜索服务条款约束。 |
| 成本 | 低至中；优先合法免费查询或最低 API 消耗。 |
| Stage 1 推荐 | `Limited`：仅用于趋势发现，不得成为 P0 事实链路的唯一来源。 |

这些来源主要用于发现趋势，不能默认作为唯一事实来源。若公开搜索结果不足以合法获取和核验，必须放弃该条目。

---

## 来源与采集方式映射

### Global

| Source | Collector | Priority | Notes |
| --- | --- | --- | --- |
| OpenAI / Anthropic / Google DeepMind Blog | RSS / Web | P0 | 原生 Feed 优先；无 Feed 时限定公开 Newsroom 页面。 |
| Microsoft AI / Meta AI / xAI / Mistral News | RSS / Web | P0 | 官方发布作为一手事实，保留原始 URL。 |
| GitHub Official Organization / Repository | Official API | P0 | 优先 Release、Tag、Commit 与仓库元数据。 |
| Hugging Face Official Organization | Official API | P0 | 优先模型、数据集与 Model Card 元数据。 |
| NVIDIA Docs / Changelog | RSS / Web | P0 | 限定官方技术更新页面。 |
| YouTube Official Channel | Official API / Feed | P0 | 只处理已登记的官方频道与公开元数据。 |
| Thibault “Tibo” Sottiaux X | Official API / Search | P1 | 仅作 Codex 动态信号；无合法官方 API 时使用公开搜索或放弃。 |
| arXiv | RSS / Feed | P1 | 论文发布可追溯；研究结论仍需分析与复核。 |
| Hacker News | RSS / Feed | P3 | 用于发现外链和讨论，不作唯一事实来源。 |
| Reddit / X Community | Search Discovery | P3 | 趋势和用户信号，需回溯一手来源。 |
| TikTok AI Trend | Search Discovery | P3 | 只用于短视频趋势发现。 |
| Global AI / Technology Media | RSS / Web | P2 | 媒体内容需交叉验证，付费墙不绕过。 |

### China

| Source | Collector | Priority | Notes |
| --- | --- | --- | --- |
| DeepSeek / Qwen / Seed / GLM Official News | RSS / Web | P0 | 原生 Feed 优先；否则限定官方公开发布页。 |
| Kimi / MiniMax / 混元 / 文心 / 盘古 Official News | RSS / Web | P0 | 保留公司、产品和开发平台的原始边界。 |
| China Official GitHub Organization | Official API | P0 | 覆盖 DeepSeek、Qwen、ByteDance Seed、Z.ai、Moonshot、MiniMax 等已登记官方组织。 |
| China Official Hugging Face Organization | Official API | P0 | 仅处理 Source Registry 已核验的官方组织。 |
| 微博官方/核心人物公开动态 | Official API / Search | P0 / P1 | 无授权官方接口时只使用合法搜索发现或放弃。 |
| 微信公众号 | Search Discovery | P3 | 仅使用公开可访问结果，不使用私有接口或登录态。 |
| 知乎 | Search Discovery | P3 | 用于专业讨论与趋势线索，不单独证实事实。 |
| B站 | Search Discovery | P3 | 发现演示、测评和用户反馈。 |
| 抖音 / 小红书 | Search Discovery | P3 | 只用于趋势与用户体验发现。 |
| China AI / Technology Media | RSS / Web | P2 | 优先公开 Feed；重要结论回溯官方发布。 |

映射表定义候选采集方式，不表示已建立连接、已获得权限或已开始采集。

---

## 降级策略

当某来源的主采集方式不可用时，只允许按以下顺序选择存在且合法的方式：

1. 官方 API。
2. RSS / Feed。
3. 公开网页。
4. 合法搜索发现。
5. 放弃该来源。

若上一级方式不存在、未授权、成本未批准或平台不允许，才可进入下一级。任何降级都不得：

- 绕过登录、验证码、付费墙、Rate Limit 或访问限制。
- 破解或伪造平台接口、签名、设备指纹或安全验证。
- 逆向或调用未授权私有 API。
- 使用他人账号、Cookie、Session、Token 或凭证。
- 因采集失败而改变安全边界。

如果合法方式全部不可用，必须放弃该来源，不得设置隐蔽或高风险降级路径。

---

## 成本原则

优先：

- 免费方案与官方免费配额。
- 开源组件，前提是其使用合法且不引入绕过访问控制的能力。
- 理论上可在 GitHub Actions 资源与运行时限内执行的轻量方案。
- 最低 API 请求量、最小转换和低频变化检测。

不默认引入：

- 高成本 SaaS。
- 付费数据服务。
- 大规模云资源、长期驻留服务或高频全站扫描。

任何付费依赖、配额升级或常驻资源都必须在后续节点单独评估和批准。

---

## Stage 1.3 输出边界

Stage 1.3 完成后已有：

- Stage 1.2 来源体系。
- Source Registry 到 Analysis Pipeline 的采集架构方案。
- 四类 Collector 的适用性、限制、成本与 Stage 1 推荐。
- Global / China 来源映射、合法降级顺序与成本原则。

Stage 1.3 完成后仍未完成：

- 实际 Collector 开发。
- 数据库、持久化或 Schema 实现。
- AI 分析、去重、信息状态判定或 Eterna 价值提取实现。
- Gmail 或其他邮件发送。
- GitHub Actions、调度器或其他自动执行。

上述未完成项属于后续 Stage，不得在 Stage 1.3 提前实现。

---

## 合规要求

以下规则为硬约束：

- 只使用公开、合法、获得授权或目标平台明确允许的数据访问方式。
- 不保存 Cookie、Session、Token 或其他账号凭证。
- 不使用他人账号或共享凭证。
- 不绕过登录、验证码、Rate Limit、付费墙、风控或其他平台安全机制。
- 不调用、逆向或伪造未授权私有接口。
- 不因采集失败、覆盖不足或成本压力改变安全边界。

---

## Stage 1.3 节点验收标准

Stage 1.3 仅在以下条件全部满足时通过：

- Source Registry → Collector Layer → Normalizer → Candidate Item → Analysis Pipeline 的层级与职责已定义。
- Official API、RSS / Feed、Web Page Monitor 和 Search Discovery 四类 Collector 已完成评估。
- Global / China 来源与 Collector 映射已建立。
- 合法降级顺序、禁止降级路径与成本原则已冻结。
- 输出边界和后续 Stage 未完成项已明确。
- 本节点未写入采集代码、配置、凭证、工作流或部署资源。
- 本节点未修改 Stage 1.1、Stage 1.2 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.4。
