# AI 情报自动化系统 · Eterna Value Extraction Rules · Stage 1.7 · v0.1

内部版本：`v0.1`

文档性质：AI 情报 Eterna 价值提取规则

状态：`FROZEN`

文档更新时间：`2026-08-11 21:09`（Asia/Shanghai）

> 本文件冻结 AI 情报系统 Stage 1.7 的 Eterna 相关性、影响域、潜在价值、风险信号与关注等级判断规则。
> 本文件属于研究/工程规划，只产生研究输入，不构成 Eterna 产品定义、架构决策、开发计划、Stage 调整或自动执行授权。

---

## 文档地位与边界

- 本文件承接 Stage 1.1–1.6 已冻结的 IntelligenceEvent、Evidence、Information Status、Confidence、Importance、What happened 与 Why it matters 语义。
- Eterna 价值判断发生在事实、事件身份、Confidence、Status、Importance 与摘要判断之后。
- 本节点只冻结判断语义、影响域和输出边界，不修改 Stage 1.1–1.6 或任何 Eterna `FROZEN` 上位文档。
- 本节点不自动修改 Eterna 路线，不自动创建开发或研究任务，不改变 Aftelle、Studio Next、Runtime Core 的当前 Stage。
- 本节点不编写 LLM Prompt，不调用模型，不实现评分算法或代码，也不开始 Stage 1.8。

---

## 权威输入与依据边界

本节点只使用仓库实际存在的以下冻结权威输入：

- `00_Eterna/Eterna_v0.6.md`
- `00_Eterna/Eterna Universe_v0.3.md`
- `01_核心领域/数字居民定义_v0.6.md`
- `02_平台产品/Studio/Studio North Star v0.3.md`
- `00_Eterna/上位文档冻结基线_v0.1.md`

附件中对应 `.txt` 已按冻结基线记录迁移为 `.md`；本文件引用当前实际路径，不恢复或推定不存在的 `.txt` 正文。

权威解释规则：

- Eterna 核心宪章提供使命、价值排序、用户权利、安全、连续性、开放协议与商业治理最高约束。
- 数字居民定义提供 Resident 身份、连续性、十三层概览、能力、数据、生命周期与产品职责边界。
- Eterna Universe 提供领域平台、公共基础设施、当前阶段主线与长期拓扑边界；长期平台清单不等于当前施工范围。
- Studio North Star 提供 Studio 长期方向、Studio Next 1.0 边界及 Appearance、Voice、ECCS 等首批能力的上位定位。
- 冻结基线限定可引用范围，并明确缺失内容不得由研究文档推定。

当前依据缺口必须显式保留：

- 仓库没有正式 Aftelle North Star；Aftelle 只能依据现有上位职责与当前主线判断，具体产品路线、Provider、架构和 Stage 细节标记为“依据不足 / 研究关联”。
- ECCS 在 Studio North Star 中具有参考系统方向与最小接入定位，但仓库没有独立的 ECCS 正式详细规范；具体字段、算法、存储和实施路线不得推定。
- Runtime Core 具有已冻结的上位职责边界，但仓库没有独立的目标架构正文；具体技术实现判断必须标记依据不足。
- 数字居民十三层只有冻结概览，没有正式详细字段与验证规范。
- 不得把索引、研究文档或 AI 日报反向解释为缺失上位定义的替代品。

---

## 处理关系

```text
Daily Report Candidate
↓
Eterna Relevance Assessment
↓
Affected Eterna Domains
↓
Potential Value / Risk / Signal
↓
Recommended Attention Level
↓
Eterna Value Extraction
```

Eterna 价值判断不得反向改变：

- `information_status`
- `current_confidence`
- `importance`
- IntelligenceEvent 身份或 `event_id`
- Evidence、CandidateItem 或原始来源

Eterna 相关性高、影响域多或潜在价值大，都不能提高事实等级、隐藏冲突 Evidence 或改变日报事件排序的事实基础。

---

## Eterna 影响域

一个 Event 可以关联多个影响域，但“与某领域相关”不等于“当前应该修改该领域”。

| 影响域 | 可判断的关联 | 权威与缺口边界 |
| --- | --- | --- |
| `Digital Resident` | 身份、人格、记忆、关系、成长、连续性、来源、迁移、治理与用户权利。 | 以核心宪章和数字居民定义为正式依据；不得把模型、Prompt 或 Agent 单独等同为 Resident。 |
| `Aftelle` | Resident 承载、交互、陪伴、恢复、备份入口及文字、语音、视觉和多模态体验。 | 只有上位职责与当前主线依据；无 Aftelle North Star，具体产品与技术判断标记依据不足。 |
| `Studio Next` | Resident 定义、编辑、验证、Build、Artifact、Release、Runtime Projection 与扩展契约。 | 以 Studio North Star 的 Next 1.0 定位为依据，不扩大其明确不要求完成的范围。 |
| `Runtime Core` | 逻辑、权限、任务、状态更新、能力调用、失败、取消、重试、降级与 Trace。 | 只有上位职责，缺少独立目标架构；不得推定具体实现或当前工程状态。 |
| `ECCS / Cognition & Continuity` | 长期认知、证据治理、记忆、知识、关系、成长、纠正、召回与连续性研究。 | Studio North Star 提供方向与最小接入边界；无独立正式详细规范时标记“依据不足 / 研究关联”。 |
| `Voice / STS` | Resident 声音身份、实时语音、Provider-neutral VoiceProfile、降级与交互能力。 | 可依据 Studio Voice Builder、Aftelle 与 Eterna Live 上位边界；具体 Provider 或路由选择不是既有正式决策。 |
| `Multimodal` | 文字、语音、视觉、动作、表情、粒子、空间形态与设备表现。 | 必须保持 Resident 本体、Layer 10 表现、Runtime Projection 和领域投影边界。 |
| `Agent / Tool Use` | Capability、Agent、工作流、工具、Adapter、权限、执行与责任。 | Agent 是 Resident 可用能力，不等于 Resident；能力扩展不得自动扩大权限。 |
| `Model / Provider` | 模型能力、API、价格、可用性、授权、迁移、降级与替代可能。 | 居民不得永久绑定单一模型或平台；情报不得自动批准替换现有 Provider。 |
| `Infrastructure / Compute` | Runtime、实时能力、云服务、算力、存储、网络、成本、休眠与恢复。 | 依据 Universe 公共基础设施边界；基础设施不得取得 Resident 所有权或制造不可迁移依赖。 |
| `Business / Competition / Ecosystem` | 商业模式、竞争产品、许可、生态、开发者市场、费用、用户控制权与平台风险。 | 商业增长必须服从核心宪章，不得以 Resident、记忆或迁移权锁定用户。 |

影响域标签只用于组织研究关联，不构成产品归属、工程 Owner、开发优先级或路线批准。

---

## 三级价值边界

Recommended Attention Level 只沿用 Stage 1.1 已冻结的三级：

### 直接有用

只有当 Event 对 Eterna 当前主线或明确已定义方向存在具体、可说明且有权威依据的价值时使用。

可以包括：

- 新 Provider、API 或模型能力可能直接改善或替代当前已明确需要的能力类别。
- 新能力能够直接缓解已由权威边界确认的技术、成本、连续性、安全或兼容问题。
- API、价格、授权、服务可用性或模型能力变化直接影响当前明确的架构选择条件或风险边界。
- 竞争产品出现与 Digital Resident、Studio、Aftelle 或连续性核心方向高度重合且可验证的新能力。
- 法律、监管、平台或生态变化直接影响用户权利、来源、授权、迁移、Provider 或基础设施边界。

必须说明：具体影响域、具体价值、当前阶段关系、权威依据和仍然存在的不确定性。“直接有用”只表示值得立即关注或进入独立评估，不等于批准采用、替换、开发或改变路线。

### 值得跟踪

适用于：

- 能力尚未成熟、尚未确认或 Evidence 仍有限。
- 当前 Stage 不适合采用，但与已冻结长期方向有关。
- 需要更多验证、成本信息、许可信息、真实使用反馈或后续发布。
- 对长期 Digital Resident、认知连续性、多模态、Agent、具身或生态方向可能重要。
- 只有研究关联，缺乏足够正式产品依据或具体 Current-stage fit。

“看起来先进”、概念相似或市场热度高，不足以升级为“直接有用”。

### 暂无行动价值

适用于：

- 与 Eterna 关系弱或只有宽泛行业背景关联。
- 当前没有可说明的技术、产品、风险、竞争或生态影响。
- 虽然新闻本身重要，但不影响 Eterna 当前主线或已定义长期方向。
- 只有重复观点、营销叙事或与权威输入无法建立具体联系的内容。

“暂无行动价值”不等于新闻不重要、事实不成立或永不相关，只表示当前 Eterna 研究没有可执行影响。

---

## 价值提取维度

每个判定与 Eterna 有关的 Event 至少回答：

| 维度 | 要求 |
| --- | --- |
| `Relevant domain` | 列出一个或多个 Eterna 影响域。 |
| `Relevance` | 说明 Event 与影响域的具体关系，并引用已有上位依据或标记依据不足。 |
| `Potential value` | 说明可能带来的技术、产品、成本、能力、连续性、用户或生态价值。 |
| `Potential risk / pressure` | 说明是否产生技术、竞争、成本、合规、生态或路线压力。 |
| `Current-stage fit` | 说明是否符合冻结的当前主线、只属于长期方向，或缺乏足够正式依据。 |
| `Attention level` | 只允许“直接有用 / 值得跟踪 / 暂无行动价值”。 |
| `Reason` | 用简洁 Evidence 与权威依据说明结论，不得只复述新闻标题。 |

多个影响域可以共享一个 Event，但每个域的依据、价值与 Current-stage fit 可以不同，不得用一个总标签掩盖差异。

---

## Current-stage fit 原则

Current-stage fit 是硬约束，必须先回答：“该 Event 是否符合 Eterna 已冻结的当前阶段主线？”

当前阶段依据只取自冻结文档明确内容：

- 稳定 Eterna 核心宪章与 Digital Resident 定义。
- 推进 Studio 产品化与 Studio Next 基础闭环。
- 推进 Aftelle 与 Runtime Core 的上位职责主线。
- 推进 Resident Instance Data Authority 的领域设计与最小验证。
- 持续验证 Resident 身份、人格、记忆、关系、状态与连续性。

Studio Next 1.0 还明确聚焦 Studio Core、领域对象、Resident Assembly、Build / Artifact / Release、Runtime Projection、扩展与边界契约，并为 Appearance、Voice 与 ECCS 最小接入建立可执行路线。

判断规则：

- 与上述明确主线具有具体关系时，说明关系，但仍不推定某个工程仓库的实际进度或当前子 Stage。
- 与长期 Universe、数字社会、Web3、具身机器人或超大规模云能力有关，但不属于当前主线时，只能标记长期重要、值得跟踪或研究信号。
- 所需产品北极星、目标架构或正式规范不存在时，标记“依据不足 / 研究关联”，不得伪造 Current-stage fit。
- 长期价值不等于当前施工优先级；Importance、竞争压力或技术先进性也不改变该边界。

任何结论不得自动要求当前开发、扩大施工范围、改变现有 Stage 或把长期平台候选转为已立项产品。

---

## “直接有用”的严格门禁

不得仅因以下原因标记“直接有用”：

- 新闻热度高。
- `importance = Critical`。
- 来自 OpenAI、Google、Anthropic 或其他大型公司。
- 模型 benchmark 宣称很强。
- 与数字居民概念相似。
- Eterna 标签或影响域数量多。
- 市场讨论、媒体报道或转载数量多。
- `information_status = Confirmed` 或 `current_confidence = High`。

“直接有用”必须同时具备：

- 可追溯 Event 与 Evidence。
- 明确 Eterna 影响域。
- 具体而非概念化的潜在价值或风险。
- 与当前主线或明确冻结方向的关系。
- 足以支持该关系的权威依据；依据不足时必须降为研究关联或值得跟踪。
- 不把研究判断写成正式决策的边界说明。

---

## 竞争情报规则

允许识别：

- 与 Eterna 类似的产品能力。
- AI Companion、Digital Human 或 Agent 平台。
- AI Studio、Builder 或创作发布平台。
- 长期记忆、Cognition 与 Continuity 能力。
- 实时语音、Voice / STS 与多模态交互。
- 多模态 Resident 表现与身份一致性。
- AI 自主执行、Tool Use 与权限治理。
- AI 生态、开发者平台和商业模式。

可以输出：

- 竞争压力。
- 可借鉴点。
- Eterna 差异化信号。
- 潜在替代技术。
- 市场验证或用户需求信号。

必须区分竞品宣称、已确认能力、独立实测和分析推断。竞品出现某项功能不等于 Eterna 必须复制，也不得自动修改 Eterna 产品定义、施工范围或 Stage。

---

## 技术机会规则

对模型、API、Provider、开源项目、新协议和基础设施，必须区分：

- `可直接评估`：与当前主线存在具体联系且 Evidence 与权威依据充分；只表示可以在独立批准后评估，不表示自动采用或替换。
- `值得后续研究`：潜在价值明确，但成熟度、事实状态、许可、成本、兼容、Current-stage fit 或正式依据仍不足。
- `当前无需处理`：缺乏具体 Eterna 影响，或只属于行业背景与远期可能性。

例如，新的实时语音模型可以说明能力变化、与 Aftelle / Voice / STS 的研究关系、潜在成本或体验价值及当前依据缺口；不得据此直接要求替换现有 Provider。

技术机会必须继续遵守 Provider-neutral、可迁移、授权透明、能力扩展不自动扩大权限以及 Resident 不永久绑定单一模型或平台的上位原则。

---

## 风险信号规则

允许提取：

- Provider 停止服务、价格变化或区域可用性变化。
- API 重大限制、Rate Limit、授权或许可变化。
- 平台政策、生态入口或第三方服务变化。
- 模型能力退化、兼容性破坏或关键能力撤回。
- 关键技术路线出现可验证的替代压力。
- 竞争产品快速接近 Eterna 核心能力。
- 法律、监管、隐私、真人声音/外貌授权或平台生态变化。
- 云、算力、基础设施或单点依赖对迁移、连续性和成本造成的压力。

风险输出必须：

- 与 IntelligenceEvent、Evidence、Information Status 和 Confidence 保持一致。
- 区分已发生风险、潜在风险、竞争压力和待验证信号。
- 说明受影响领域、可能影响与当前依据。
- 保留冲突、不确定性与原始来源。

未确认消息不得写成确定风险事实；高风险也不得自动触发路线调整、Provider 替换、工程任务或安全边界降低。

---

## 日报 Eterna 价值提取区块

Global 与 China 日报分别使用以下结构：

```text
## Eterna 价值提取

### 直接有用
- Event
- 影响域
- 价值
- 当前阶段关系
- 依据

### 值得跟踪
- Event
- 影响域
- 为什么值得跟踪
- 当前阻碍 / 不确定性

### 暂无行动价值
- Event
- 简要原因

### Eterna 今日主控判断
- 是否存在值得立即关注的技术变化
- 是否存在需要持续观察的信号
- 是否存在竞争 / Provider / 生态风险
```

“Eterna 今日主控判断”只是研究摘要，不是自动批准、正式决策或控制指令。不得输出：

- 自动批准修改路线或正式定义。
- 自动进入新 Stage 或改变当前 Stage。
- 自动创建工程、开发或研究任务。
- 自动修改产品计划、架构、ADR 或 `FROZEN` 文档。

---

## Global / China 边界

- Global Report 只基于 Global Event 生成自己的 Eterna 价值提取。
- China Report 只基于 China Event 生成自己的 Eterna 价值提取。
- 两次日报分别判断影响域、价值、风险、Current-stage fit 与 Attention level。
- Stage 1.7 不合并 Global / China Event、价值区块或“今日主控判断”。

---

## 事实与推断边界

每项价值提取必须显式区分：

| 内容层 | 要求 |
| --- | --- |
| Event 已确认事实 | 只陈述 Evidence 与当前 `information_status` 支持的事实，并保留原始来源。 |
| 情报系统分析推断 | 明确使用“可能、推测、显示出、值得验证”等非事实措辞。 |
| 对 Eterna 的潜在影响 | 说明条件、影响域与权威依据，不写成已批准影响。 |
| 尚待验证的研究判断 | 标记不确定性、证据缺口、权威缺口和后续观察条件。 |

可以写：“该模型能力可能降低 Aftelle STS Provider 成本，值得独立验证。”

不得写：“该模型将取代当前 Aftelle Provider。”除非未来同时存在充分 Evidence 和独立正式决策；Stage 1.7 本身无权作出该决策。

Eterna 价值分析不得把推断重新包装成事实，也不得因 Eterna 高相关而降低事实标准。

---

## 权威与正式变更边界

AI 日报及 Eterna Value Extraction 位于 `06_研究与探索`，属于研究输入，不是：

- 产品定义。
- 架构决策或 ADR。
- 开发计划或任务。
- 当前 Stage 调整。
- `FROZEN` 文档修改。
- Provider、模型、API 或基础设施采购与替换决定。

若未来某条情报可能影响正式路线，必须经过独立审核、权威依据补全、影响评估和仓库正式变更流程。日报本身不得触发、批准或执行该流程中的任何变更。

---

## 合规边界

以下规则为硬约束：

- 不因 Eterna 价值分析需要重新获取受限内容。
- 不绕过登录、验证码、Rate Limit、付费墙、访问控制或其他安全机制。
- 不调用、逆向或伪造未授权私有 API。
- 不保存 Cookie、Session、Token、API Key、密码或其他认证凭证。
- 不使用不可追溯信息形成确定性 Eterna 判断。
- 不让模型或人工流程补造缺失事实、来源正文、Eterna 权威定义或当前工程状态。
- 只依据公开、合法取得的 Event Evidence 和仓库实际存在的权威输入判断。
- 不因 Eterna 高相关、潜在价值或风险紧迫而降低事实与合规标准。

---

## Stage 1.7 明确不做

- 不编写 LLM Prompt。
- 不调用 OpenAI、Gemini、Claude 或其他模型。
- 不定义数值评分、权重公式或阈值。
- 不实现 Python、TypeScript、Swift 或其他业务代码。
- 不实现 Eterna 自动决策。
- 不自动调整 Eterna 路线、产品定义或 Stage。
- 不自动创建开发、工程或研究任务。
- 不修改 Aftelle、Studio、Runtime Core 或其他产品计划。
- 不生成真实日报。
- 不实现 Gmail 发送。
- 不创建 GitHub Actions、定时任务或其他自动化。
- 不定义或开始 Stage 1.8 内容。

本节点只冻结 Eterna 价值提取规则与输出边界。

---

## Stage 1.7 节点验收标准

Stage 1.7 仅在以下条件全部满足时通过：

- Eterna 影响域完整，并对缺失 Aftelle、ECCS、Runtime 详细正式依据作出明确标记。
- “直接有用 / 值得跟踪 / 暂无行动价值”三级边界与直接有用严格门禁明确。
- Current-stage fit 与“长期价值不等于当前施工优先级”原则明确。
- 技术机会、竞争情报与风险信号规则明确。
- Global / China 分别生成 Eterna 价值提取，未跨 Region 合并。
- Event 事实、分析推断、潜在 Eterna 影响与待验证研究判断明确分离。
- AI 情报不会自动修改 Eterna 路线、产品定义、Stage、任务或任何 `FROZEN` 文档。
- 本节点未进入 Prompt、模型调用、评分算法、代码、Schema、数据库或真实日报实现。
- 本节点未修改 Stage 1.1–1.6 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.8。
