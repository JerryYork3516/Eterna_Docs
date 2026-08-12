# AI 情报自动化系统 · Implementation Plan and Dependency Freeze · Stage 1.11 · v0.1

内部版本：`v0.1`

文档性质：AI 情报自动化系统实现方案与依赖冻结规范

状态：`FROZEN`

文档更新时间：`2026-08-12 10:16`（Asia/Shanghai）

> 本文件只冻结进入 Stage 1.12 前的最小实现技术栈、目录、依赖、接口、状态与测试门禁。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、上位承诺、业务代码、Workflow、Secret、外部 API 调用或实际自动化实现。

---

## 1. 适用范围与继承边界

- 本规范位于 `06_研究与探索/AI_情报`，完整继承 Stage 1.1–1.10 已冻结的目标、来源、采集、数据、聚类、分析、价值提取、日报、Gmail 与 Git 规则。
- Docs Markdown 日报仍是长期研究归档；Gmail 仍只是对应日报的摘要投影。
- Global 与 China 从来源、状态、报告、Git 到邮件投递保持两条独立链。
- 本节点不修改 Stage 1.1–1.10 或任何 Eterna 上位 `FROZEN` 文档，不改变 Eterna 正式定义。
- 未发现 Stage 1.1–1.10 之间阻止本方案成立的语义冲突。
- 本节点只冻结方案，不创建代码、目录骨架、依赖文件、Workflow、Secret 或实际任务，也不开始 Stage 1.12。

---

## 2. 主实现语言

### 2.1 比较

| 维度 | Python | Node.js |
|---|---|---|
| RSS、HTTP 与文本处理 | 标准库与成熟轻量库覆盖直接 | 原生 `fetch` 可用，但 Feed、类型与构建工具通常增加依赖 |
| 数据标准化与离线处理 | `datetime`、`json`、`hashlib`、`email`、`zoneinfo` 可直接使用 | 可实现，但 TypeScript 通常需要编译与额外工具链 |
| GitHub Actions | 官方 Runner 与 `setup-python` 可直接运行 | 官方 Runner 可直接运行 |
| 单脚本自动化 | 无需编译，适合每天两次短任务 | JavaScript 无需编译；TypeScript 需要构建步骤 |
| 维护面 | 可用少量依赖完成端到端任务 | 若同时保证类型、测试和 Feed 处理，依赖面通常更大 |

### 2.2 冻结结论

- Stage 1 主实现语言冻结为 `Python 3.13.x`。
- 不维护 Node.js 第二实现，不引入 TypeScript 构建链。
- Stage 1.12 使用 GitHub-hosted Runner 上的 CPython，并固定到 `3.13` 小版本线；升级主/次版本必须重新通过依赖与离线测试门禁。
- Python 3.13 的选择依据是单语言、无需编译、标准库覆盖充分，且处于官方维护周期。

---

## 3. 代码与产物目录

未来实现目录冻结为：

```text
06_研究与探索/AI_情报/
├── Stage1/                         # FROZEN 规则文档；自动化只读
├── reports/
│   ├── global/YYYY/MM/             # Global 正式日报
│   └── china/YYYY/MM/              # China 正式日报
├── automation/
│   ├── pyproject.toml              # 项目元数据与直接依赖声明
│   ├── requirements.lock           # 精确版本与哈希锁定
│   ├── config/
│   │   ├── global_sources.json     # 人工维护的 Global 运行配置
│   │   └── china_sources.json      # 人工维护的 China 运行配置
│   ├── collectors/                 # 来源适配器；不得包含分析逻辑
│   ├── pipeline/                   # 模型、标准化、聚类、分析与编排
│   ├── rendering/                  # Markdown 日报与 Email Projection
│   ├── delivery/                   # Gmail 与 Git 边界适配器
│   ├── state/
│   │   ├── global.json             # Global 非敏感持久状态
│   │   └── china.json              # China 非敏感持久状态
│   └── tests/
│       └── fixtures/               # 固定、公开、可离线重复的数据
└── README.md                       # AI 情报区域入口与运行说明
```

约束：

- `Stage1/**`、`automation/**` 与 `reports/**` 分离；冻结规则、人工配置、代码、状态和生成报告不得混放。
- 自动化代码不得散落仓库根目录，不创建空目录占位。
- `config/**` 只允许人工审核变更，日报任务只读，不得自动改写。
- Stage 1.10 的日报写入范围继续有效。本节点另行批准未来自动化只写两个状态文件：`automation/state/global.json` 与 `automation/state/china.json`；不得据此扩大到其他 `automation/**` 路径。
- 状态文件只能与对应 Region 本次日报作为同一允许产物提交；无有效变化不得改写。
- Secret 不进入上述任何目录。

---

## 4. Collector 实现分层

```text
Source Registry / Read-only Config
→ Transport
→ Source Adapter
→ Normalizer
→ CandidateItem
```

- `Transport`：统一超时、User-Agent、响应大小、Rate Limit 与错误分类；不得绕过访问限制。
- `Source Adapter`：只理解单一来源或同类公开协议，将原始响应映射为中间记录。
- `Normalizer`：按 Stage 1.4 生成 CandidateItem，补齐 Region、来源引用与标准时间。
- Collector 不执行事实升级、事件聚类、摘要或 Eterna 价值判断。
- 单个来源失败只形成可追踪的 Collection Failure，不改变 Global / China 隔离或合规边界。

### 4.1 Official API

- 首版用于 GitHub、Hugging Face 及明确开放的官方 API。
- YouTube 与未来合法 X API 只在权限、配额和 Secret 获得批准后接入。
- API 返回的对象 ID、发布时间、原始 URL 和官方主体必须保留。

### 4.2 Native RSS / Atom

- 首版优先用于官方 Blog、Newsroom、arXiv、Hacker News 与支持 Feed 的媒体。
- Feed 内容不自动等同于官方事实；事实资格仍由 Source Registry 与 Evidence 规则决定。

### 4.3 RSSHub

- 只作为公开、合法、经逐来源确认的补充适配器。
- 不是核心依赖，不是任何 Region 的单点依赖；不可用时回到原生 Feed、公开网页、合法搜索或放弃来源。

### 4.4 Public Web Monitor

- 只处理无 Feed 的高价值公开官方页面、Changelog 与 Newsroom。
- 首版仅支持静态、可稳定定位的公开内容；动态登录页、验证码页、付费墙与反自动化页面直接放弃。
- 不引入浏览器自动化作为默认能力。

### 4.5 Search Discovery

- 仅通过经批准的合法搜索服务接口发现 TikTok、抖音、小红书、微信公众号、知乎、Reddit、X 等趋势信号。
- 搜索结果默认不是事实 Evidence；必须回到可访问原始来源或更高等级来源核验。
- Search Discovery 不属于 Stage 1 MVP 必需链路。

---

## 5. MVP Collector 与来源范围

### 5.1 MVP 必须可运行

| Region | Collector | 首版范围 |
|---|---|---|
| Global | Native RSS / Atom | Source Registry 中可稳定访问的官方 Blog、arXiv、Hacker News 与已登记 Feed |
| Global | Official API | GitHub 官方组织/仓库、Hugging Face 官方组织及公开对象 |
| Global | Public Web Monitor | 少量无 Feed、静态且公开的 P0 官方更新页 |
| China | Native RSS / Atom | Source Registry 中实际提供且可合法访问的国内官方 Feed |
| China | Official API | 国内公司在 GitHub、Hugging Face 等官方组织的公开发布 |
| China | Public Web Monitor | DeepSeek、Qwen、Seed/豆包、GLM、Kimi、MiniMax、混元、文心、盘古等已登记主体的少量公开官方更新页 |

首版不要求清单中的每个主体都具备自动 Collector；每条 Region 链必须覆盖一批稳定 P0/P1 来源，并能在来源缺口时正确生成 `Partial` 或 `No valid report`。

### 5.2 MVP 条件接入

- YouTube Data API：仅在官方项目、配额与凭证获批后接入。
- Search API：仅在合法性、成本、结果追溯和 Secret 获批后接入。
- RSSHub：仅在逐来源确认内容公开且路径稳定后接入。
- 需要额外账号或 Key 的 GitHub / Hugging Face 配额提升：不是匿名公开读取的前置条件，获批后才启用。

### 5.3 Later / Discovery

- X、TikTok、抖音、小红书、微信公众号、知乎、微博及其他权限或平台限制较大的来源。
- Reddit 等需要额外 API 政策核验或稳定授权的社区来源。
- 任何只能依赖 Cookie、个人 Session、私有 API、逆向签名或浏览器自动登录的来源。

封闭平台暂时不能合法自动获取，不得阻塞 Stage 1 MVP 上线。

---

## 6. 最小第三方依赖

### 6.1 冻结清单

| 依赖 | 冻结版本线 | 用途 | 必须 | License / 开源 | 运行时网络 | 账号 / Key | 免费额度 | 替代方案 |
|---|---|---|---|---|---|---|---|---|
| Python 标准库 | `3.13.x` | JSON、时间、哈希、路径、Email、子进程 | Yes | PSF License / Yes | No | No | 不适用 | 无第二语言实现 |
| `httpx` | `0.28.x` | 有超时与连接管理的 HTTP 客户端 | Yes | BSD-3-Clause / Yes | Yes | 依来源而定 | 依来源而定 | `urllib.request` |
| `feedparser` | `6.0.x` | RSS / Atom 解析 | Yes | BSD-style / Yes | No；下载由 HTTP 层负责 | No | 不适用 | 标准库 XML，仅作故障替代 |
| `openai` | `2.x` | 首个 LLM Provider 的官方 API SDK | MVP 分析链 Yes | Apache-2.0 / Yes | Yes | OpenAI API credential | 不假设存在免费额度 | 另一经批准的官方模型 API Adapter |
| `google-api-python-client` | `2.x` | Gmail API 官方客户端 | Gmail 链 Yes | Apache-2.0 / Yes | Yes | Google OAuth credential | 受官方配额约束，不视为无限免费 | 官方 Gmail REST + `google-auth` |
| `google-auth` / `google-auth-oauthlib` / `google-auth-httplib2` | 当前兼容主版本 | Gmail OAuth 2.0 与客户端认证 | Gmail 链 Yes | Apache-2.0 / Yes | Yes | Google OAuth credential | 同 Gmail API 配额 | 经批准的 Google 官方认证方式 |
| `pytest` | `9.x` | Unit、Fixture 与 Offline 测试 | Dev Yes | MIT / Yes | No | No | 不适用 | 标准库 `unittest` |

### 6.2 版本与安装纪律

- 本节点冻结运行时、直接依赖及主版本线，不创建 `pyproject.toml`、`requirements.lock` 或虚拟环境。
- Stage 1.12 第一步必须解析兼容的精确补丁版本与传递依赖，并在 `requirements.lock` 中固定版本和哈希；未完成锁定不得进入网络集成测试。
- 依赖升级必须通过 Offline Fixture、许可证、漏洞与行为回归检查；主版本升级需要重新审核本规范。
- 生产安装使用锁文件，不在 Workflow 中无界安装 `latest`。
- Git 操作使用 Runner 已安装的 `git` CLI；不引入 GitPython。
- JSON 配置、状态、时间、路径、邮件 MIME 与 HTML 基础解析优先使用标准库，不引入 YAML、ORM、数据库框架或 Web 框架。

### 6.3 禁止的默认依赖

- Selenium、Playwright、Puppeteer、无头浏览器。
- 未经批准的爬虫 SaaS、逆向 SDK、私有 API Wrapper。
- 向量数据库、embedding 框架、Agent 框架与大型数据库服务。
- 来源不明、许可证不清或以绕过平台访问控制为核心能力的包。

---

## 7. LLM 接口边界

- Pipeline 只依赖内部 `LLMProvider` 边界，不让业务规则直接绑定 SDK 对象。
- Stage 1 MVP 首个 Adapter 冻结为 OpenAI 官方 API 的 Responses API，通过官方 `openai` Python SDK 调用。
- 具体模型 ID、预算上限、请求超时与输出上限进入人工维护的非敏感配置；API credential 只进入 Secret。
- LLM 只用于内容分类、Event 辅助判断、Status / Confidence / Importance 辅助分析、摘要、Why it matters 与 Eterna Value Extraction。
- 所有 LLM 结果必须经过 Stage 1.4–1.8 的状态、来源、追溯与报告校验；模型不能自动将社区或搜索结果提升为事实。
- LLM 不得绕过访问限制、补造缺失正文、生成不存在的 URL、覆盖 Evidence、直接修改 Eterna 正式文档或执行研究结论。
- 禁止使用 ChatGPT Cookie、Codex Session、网页登录、个人登录 Session 或 Codex / ChatGPT 订阅额度作为程序 API。
- 若没有获批的官方 API credential 或预算，分析链应明确失败，不得降级到个人会话凭证。

---

## 8. Search Provider 边界

- 内部只定义 `SearchProvider` 接口：查询、Region、时间窗口、结果 URL、标题、摘要、发布时间线索与 Provider 元数据。
- 候选服务必须提供官方 API、明确自动查询许可、可审计配额/价格与可追溯结果 URL。
- Search credential、查询预算和 Provider 配置必须分别管理；不得把 Key 放入来源清单。
- Stage 1 MVP 冻结为 `No Search Provider dependency`；没有合适 Provider 时直接跳过封闭平台 Discovery。
- Search 结果只用于发现，不自动成为 Confirmed Evidence；无法回到合法原始来源时保持信号/趋势或放弃。

---

## 9. Gmail 实现方案

- 首选方案冻结为 Google 官方 Gmail API，通过官方 Python 客户端与 OAuth 2.0 发送 Stage 1.9 定义的 Email Projection。
- 只申请发送和完成幂等核验所需的最小授权范围；实际 Scope 必须在 Stage 1.12 实现前单独核对。
- OAuth Client、Refresh Credential 与收件人配置只进入 GitHub Actions Secrets / Environment Secrets。
- Fallback 只允许 Google 官方支持、使用 OAuth 2.0 的发送方式，并需单独审核；不得自动切换到密码或弱认证。
- 禁止保存 Gmail 密码、个人浏览器 Cookie，禁止自动网页登录 Gmail 或绕过 Google 安全验证。
- Gmail 失败只重试投递步骤，不重新采集、分析、生成或提交日报。

---

## 10. 最小状态持久化方案

### 10.1 方案评估

| 方案 | 结论 |
|---|---|
| 仓库内非敏感状态文件 | 可审计、跨运行持久；按 Region 分片后适合当前低频 MVP |
| GitHub Artifact / Cache | 适合短期运行与投递回执；存在保留期、淘汰与非权威性，不可单独承载长期事件历史 |
| SQLite | 单机事务清晰，但二进制 Git diff、Global / China 写冲突与合并风险不适合当前主仓库 |
| 外部数据库 | 增加服务、Secret、成本和运维，不符合 Stage 1 MVP |

### 10.2 冻结结论

Stage 1 MVP 使用一套组合式轻量方案：

1. `automation/state/global.json` 与 `automation/state/china.json` 保存长期、非敏感、可审计状态。
2. GitHub Actions Artifact 保存单次 Run 与 Gmail 投递回执，供短期故障恢复；Artifact 不是事实来源或长期研究归档。
3. 报告存在性、元数据、文件哈希与 Git 历史仍是正式日报是否归档成功的权威依据。

### 10.3 持久状态内容

- Canonical URL、Source Object ID 或不可逆内容指纹。
- `first_seen_at`、`last_seen_at`、重复观察能力。
- Candidate / Evidence / Event 的稳定 ID 与来源引用关系。
- `status_history` 及触发状态变化的 Evidence ID。
- `Region + report_date + revision` 幂等键、报告路径与内容哈希。
- Git commit 结果、上一次已对账的非敏感 Delivery Status 与投递幂等键。

不得写入：

- Cookie、Session、API Key、OAuth Client Secret、Refresh Token、密码或收件人地址。
- 受限正文、完整 API 请求/响应、未经必要性审核的个人信息。
- LLM 隐藏推理、原始认证错误载荷或其他可能泄露凭证的内容。

### 10.4 生命周期与冲突控制

- Event、报告、Revision 和状态历史随对应 Docs 归档长期保留；不得静默覆盖。
- 可重建的临时下载、LLM 中间响应与单次缓存不进入 Git，Run 结束后按 Artifact 保留策略清理。
- Global 任务只能写 `global.json`，China 任务只能写 `china.json`。
- 状态与对应报告在同一 Git 提交中更新；邮件成功后的即时回执写入该 Run 的 Artifact，不为此制造第二个无意义 Git commit。
- 后续对应 Region 的正常报告提交可把已核验 Artifact 回执对账到 JSON；若只需重试邮件，则以 Artifact 和 Gmail 幂等核验为依据，不改写日报或制造状态空提交。
- 同一 `Region + report_date` 继续受 Stage 1.10 并发锁约束；发生非快进或状态冲突时安全失败，不自动覆盖。

---

## 11. Git 与 `main` 风险

- 直接给予自动化 `contents: write` 到 `main` 存在夹带修改、非快进、分支保护冲突和供应链权限扩大风险。
- Stage 1 MVP 推荐保持 Stage 1.10 已冻结的 `main` 目标分支，以减少双分支和自动合并复杂度，但必须在实现前完成硬门禁：
  - 核对实际 branch protection / ruleset 是否允许批准的自动化身份按预期写入。
  - 使用最小 `contents: write`，并在提交前校验仅含当前 Region 报告与对应状态文件。
  - Pull / rebase 后再次校验路径与幂等键；冲突时安全失败，不 force push。
  - 人工未提交变更、规则文件变化或未知文件出现时拒绝提交。
- 若 `main` 保护要求、多人并发频率或安全审计无法满足以上门禁，后续必须先通过治理变更切换为 `automation branch + reviewed merge`；Stage 1.11 不修改 branch protection，也不自行创建分支。

---

## 12. Secret 类别与最小权限

只登记以下类别，不冻结或猜测真实名称和值：

- LLM credential。
- Search credential（MVP 可不存在）。
- Gmail OAuth credential。
- Recipient configuration。
- GitHub / Hugging Face / YouTube 等可选第三方 API credential。

硬约束：

- Secret 只能进入 GitHub Actions Secrets、Environment Secrets 或后续正式批准的受保护环境变量系统。
- 禁止进入提交的 `.env`、Markdown、Python、YAML 明文、配置、状态、日报、日志、Email 或 Commit message。
- Workflow 只在需要该 Secret 的最小 Job / Step 注入；Global / China 不得无条件共享无关凭证。
- Repository 权限默认只读；仅 Git 写入步骤临时需要有限 `contents: write`。
- 日志和异常必须脱敏，不打印环境变量、请求 Authorization Header 或 OAuth 载荷。

---

## 13. 配置与 Source Registry

### 13.1 冻结治理文档

- Stage 1.1–1.11 文档及 Source Registry 是人工审核的治理输入。
- 自动化只能读取，不能回写、重排或根据运行结果自动修改。

### 13.2 机器可读运行配置

- `global_sources.json` 与 `china_sources.json` 从 Source Registry 人工派生，只保留运行所需的来源 ID、Region、Collector 类型、公开 URL、启用状态和非敏感参数。
- 配置必须引用稳定的 Source Registry 标识，不能替代 Registry 的用途、Priority、Credibility 与事实引用规则。
- 配置变更必须由人工提交并接受一致性检查；日报任务不得新增来源或改变来源优先级。
- API Key、收件人、账号和任何认证信息不得出现在配置中。

---

## 14. 测试体系与门禁

### 14.1 Unit

必须覆盖：

- URL normalization、Source Object ID 与内容指纹。
- `source_published_at`、`collected_at`、`first_seen_at`、`last_seen_at` 及时区解析。
- Region 隔离、状态映射、报告路径、Revision 与幂等键。
- Exact / Near / Same Event 规则边界及 Eterna 标签不参与事件身份判断。

### 14.2 Fixture / Offline

- 使用固定本地数据验证 `CandidateItem → Evidence → IntelligenceEvent → IntelligenceReport → Email Projection`。
- 默认测试必须阻断真实网络、真实 Git push、Gmail、Search 与 LLM 调用。
- Offline 测试必须可在无 Secret 环境重复执行。

### 14.3 Integration

- 只针对经批准的公开 RSS / API 进行有限、低频、显式启用的测试。
- 必须使用测试配置、超时、请求上限和脱敏日志；失败不得触发绕过或高频重试。
- 有 Secret 的 Integration Job 与默认 PR / Offline Job 隔离。

### 14.4 End-to-End

- 最终覆盖 `Collect → Analyze → Report → Git → Gmail`，Global / China 分别验收。
- 必须使用受控日期、测试收件配置、测试目标或明确批准的真实路径，验证幂等、重试与失败恢复。
- Stage 1.11 不执行真实端到端测试。

### 14.5 合并与发布门禁

Stage 1.12 每个实现增量至少满足：

1. Unit 与 Offline Fixture 全部 PASS。
2. 默认测试无网络、无 Secret，且无真实外部副作用。
3. 报告 Fixture 通过 Stage 1.8 结构与来源追溯校验。
4. Global / China 交叉写入测试必须失败。
5. 敏感值扫描、允许路径检查和 `git diff --check` PASS。
6. Integration 与 End-to-End 只在显式授权环境运行；未运行不得伪报 PASS。

---

## 15. Fixture 范围

未来固定数据集必须包含：

- Confirmed、Unconfirmed、High-confidence signal 与 Community trend。
- `Contradicts` Evidence、状态演进与历史保留。
- Exact Duplicate、Near Duplicate 与 Same Event, Different Evidence。
- Partial source failure 与 `No valid report`。
- Gmail failure、Git failure、重复 Run 与 Revision。
- Global / China 同名实体或相似事件，验证不得跨 Region 聚类或写入。

Fixture 只能使用许可允许的公开片段、合成数据或脱敏记录，不包含 Secret、受限内容、真实收件人或认证信息。

---

## 16. Stage 1.12 实现顺序

Stage 1.12 开发顺序冻结为：

1. 建立最小 Python 代码骨架、`pyproject.toml` 与精确依赖锁。
2. 实现 Global / China 配置加载、Registry 引用与允许路径校验。
3. 实现 Stage 1.4 数据模型及序列化。
4. 实现 Region 分片状态、幂等键、Revision 与恢复边界。
5. 实现 Native RSS / Atom、GitHub / Hugging Face API 与有限 Public Web MVP Collector。
6. 实现 Normalizer 与 CandidateItem 追溯链。
7. 实现去重、Evidence 与 Event 聚类规则。
8. 实现 LLMProvider 接口和首个官方 OpenAI API Adapter。
9. 实现 Status / Confidence / Importance、摘要与 Eterna Value Extraction。
10. 实现 Markdown 日报渲染与结构校验。
11. 实现 Gmail Email Projection 与 Gmail API Delivery Adapter。
12. 实现受限 Git commit / push Adapter。
13. 实现 Global / China 独立 Pipeline 编排和针对性失败恢复。
14. 补齐并锁定 Unit、Fixture / Offline 测试门禁。
15. 运行获批的有限 Integration 测试。
16. 创建并审核 GitHub Actions Workflow、调度、权限、并发与人工触发。
17. 在独立批准后执行 Global / China End-to-End Validation。

第 1–13 步必须同步增加对应 Unit / Offline Fixture；第 14 步是完整门禁收口，不代表测试可以延后补写。

不得跳过离线门禁直接创建具有写权限或 Secret 的 Workflow。

---

## 17. Stage 1 MVP 完成定义

Stage 1 第一版不要求所有平台都可采集。MVP 必须同时满足：

- Global 08:00 与 China 20:00 两条每日链路独立成立。
- 每条链覆盖一批高价值、稳定、合法的官方 / Feed / API 来源。
- 能生成符合 Stage 1.8 的日报并写入 Docs。
- 能在允许路径内安全 commit / push，并保持幂等与 Revision。
- 能生成符合 Stage 1.9 的 Email Projection 并通过 Gmail API 投递。
- 能区分事实、信号、传闻和趋势，保留完整来源追溯。
- 能生成受 Stage 1.7 约束的 Eterna 价值提取。
- 来源失败能输出 `Partial`、`No valid report` 或 `Failed` 的正确语义。
- 整条链路不违反 OpenAI、Google、GitHub 或第三方平台规则。

X、TikTok、抖音、小红书、微信公众号、知乎、微博和其他封闭平台的完整覆盖率不是 MVP PASS 门槛。

---

## 18. 合规硬约束

- 只使用公开、合法、授权或平台明确允许的数据访问与模型调用方式。
- 不破解平台接口，不逆向签名、设备指纹或私有协议。
- 不绕过登录、验证码、付费墙、访问控制、Rate Limit 或风控。
- 不盗用、保存或共享 Cookie、Session、Token、API Key、账号密码或 ChatGPT / Codex 凭证。
- 不把个人 Codex / ChatGPT 会话、登录状态或订阅额度作为运行时后端。
- 不因采集、分析、Git 或 Gmail 失败降低安全标准或切换到违规方案。
- 依赖若以绕过平台控制、模拟个人登录或调用未授权私有 API 为核心能力，不得进入正式依赖清单。
- LLM、搜索与社区内容不得覆盖原始 Evidence，不得伪造缺失上下文或自动修改 Eterna 正式路线与 `FROZEN` 文档。

---

## 19. 本节点明确不做

Stage 1.11 不做：

- Python、TypeScript 或其他业务实现。
- 真实代码骨架、`pyproject.toml`、requirements、lockfile 或依赖安装。
- `.github/workflows/*.yml`、cron、GitHub Actions 或 branch protection 配置。
- Secret、API Key、OAuth、Gmail、Search 或 LLM 配置与调用。
- Collector、数据库、Prompt、报告生成器、自动 commit 脚本或真实日报。
- Unit、Integration、End-to-End 或实际定时执行。
- Stage 1.12 的任何实现内容。

---

## 20. Stage 1.11 验收

Stage 1.11 只有同时满足以下条件才可 PASS：

- 主实现语言与单语言边界已冻结。
- 自动化目录、代码 / 配置 / 状态 / 报告分离已冻结。
- MVP Collector、条件接入与 Later / Discovery 范围已冻结。
- 最小直接依赖、许可、网络、账号、成本与替代方案已登记。
- LLM、Search 与 Gmail 接口及安全边界已冻结。
- 非敏感状态、短期投递回执、生命周期与 Git 冲突边界已冻结。
- `main` 风险、MVP 推荐与切换条件已冻结。
- Secret 类别、最小权限和机器配置边界已冻结。
- Unit、Offline、Integration、End-to-End 与 Fixture 门禁已冻结。
- Stage 1.12 确定实现顺序与 MVP 完成定义已冻结。
- 未创建代码、Workflow、Secret、依赖文件或外部 API 调用。
- 未修改任何 Eterna 上位 `FROZEN` 文档，未开始 Stage 1.12。

---

## 21. 官方核验依据

- [Python 官方版本状态](https://devguide.python.org/versions/)
- [Node.js 官方发布周期](https://nodejs.org/en/about/previous-releases)
- [feedparser 官方仓库与 License](https://github.com/kurtmckee/feedparser)
- [HTTPX 官方仓库](https://github.com/encode/httpx)
- [OpenAI 官方 Python SDK](https://github.com/openai/openai-python)
- [Google Gmail API Python Quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [pytest 官方仓库](https://github.com/pytest-dev/pytest)

上述链接只用于核验运行时、SDK、许可证与官方接入边界，不构成对外部服务额度、价格或永久可用性的承诺；实现前仍须再次核验。
