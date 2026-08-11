# AI 情报自动化系统 · Source Registry · Stage 1.2 · v0.1

内部版本：`v0.1`

文档性质：AI 情报来源注册与治理规范

状态：`FROZEN`

文档更新时间：`2026-08-11 09:57`（Asia/Shanghai）

> 本文件建立 AI 情报系统 Stage 1.2 的来源分类、优先级、字段、初始清单与合规边界。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、上位承诺、采集授权或技术接入方案。

---

## 文档地位与边界

- 本文件承接已冻结的 Stage 1.1，不修改 Stage 1.1 或任何 Eterna `FROZEN` 上位文档。
- 本节点只定义来源注册体系，不开发采集程序，不接入 API，不配置 RSSHub，不实现自动化。
- 本节点不设计 Stage 1.3 的采集层、调度、鉴权、抓取、去重或存储实现。
- 登记 URL 只表示公开入口，不表示已获得自动采集或内容再利用授权。

---

## 来源字段规范

每个来源至少包含以下字段：

| 字段 | 必填 | 规范 |
| --- | --- | --- |
| `Name / 名称` | Yes | 可唯一识别的来源、组织、人物或频道名称。 |
| `Type / 类型` | Yes | `Official`、`Person`、`Community` 或 `Media`。 |
| `Region / 地区` | Yes | `Global` 或 `China`。 |
| `Platform / 平台` | Yes | 官网、Blog、Docs、GitHub、Hugging Face、X、Reddit 等公开承载位置。 |
| `URL` | Conditional | 已知时登记公开 URL；无法确认时标记“待核验”，不推测私有入口。 |
| `Priority / 来源等级` | Yes | `P0`–`P3`，按本文件统一定义。 |
| `Usage / 用途` | Yes | 说明用于事实核验、早期信号、技术发现、趋势或行业分析。 |
| `Credibility / 可信度` | Yes | `High`、`Medium` 或 `Low`；不能替代单条情报的状态判定。 |
| `Fact Citation / 是否允许作为事实引用` | Yes | `Yes`、`Conditional` 或 `No`。 |
| `Eterna Tags / Eterna 关联标签` | Yes | 至少使用一个本文件冻结的 Eterna 标签。 |
| `Notes / 备注` | Yes | 记录权威边界、核验条件、访问限制或其他风险。 |

### 事实引用规则

- `Yes`：可在其自身权威范围内作为一手事实来源，但仍需保留原始 URL 与发布时间。
- `Conditional`：只能作为信号，或经官方/其他独立来源交叉核验后作为事实引用。
- `No`：只用于发现趋势、讨论或线索，不得单独成为事实依据。

---

## 来源优先级

| 优先级 | 定义 | 事实边界 |
| --- | --- | --- |
| `P0` | 官方发布、官方仓库、官方文档。 | 在发布方自身权威范围内可作为一手事实来源。 |
| `P1` | 核心人物、研究人员、可信技术社区或研究入口。 | 默认为高价值信号，不因身份或平台自动成为事实。 |
| `P2` | AI 专业媒体、科技媒体、行业分析。 | 需回溯原始材料或交叉验证。 |
| `P3` | 社区趋势、短视频平台、用户讨论。 | 可发现趋势，但不能单独作为事实依据。 |

优先级表示默认监控价值，不等于单条内容的事实状态。

---

## 官方来源（Official）

### Global

| Source | Type | Region | Platform / URL | Priority | Usage | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI | Official | Global | [Website](https://openai.com/)；[News](https://openai.com/news/)；[Developer](https://developers.openai.com/)；[GitHub](https://github.com/openai)；[Hugging Face](https://huggingface.co/openai) | P0 | 模型、产品、API、Codex、研究事实 | High | Yes | Agent / AI Coding / Voice / STS / Multimodal / Business / Ecosystem | 仅对 OpenAI 自身发布具有一手权威。 |
| Anthropic | Official | Global | [Website](https://www.anthropic.com/)；[News](https://www.anthropic.com/news)；[Docs](https://docs.anthropic.com/)；[GitHub](https://github.com/anthropics)；[Hugging Face](https://huggingface.co/anthropic) | P0 | Claude、Agent、AI Coding、安全研究 | High | Yes | Agent / AI Coding / Business / Ecosystem | 第三方对 Claude 的测评不属官方事实。 |
| Google DeepMind / Gemini | Official | Global | [DeepMind](https://deepmind.google/)；[Blog](https://deepmind.google/discover/blog/)；[Gemini Docs](https://ai.google.dev/gemini-api/docs)；[GitHub](https://github.com/google-deepmind)；[Hugging Face](https://huggingface.co/google) | P0 | 模型、研究、Gemini、多模态 | High | Yes | Multimodal / Agent / Voice / STS / Business / Ecosystem | 区分 DeepMind 研究、Google AI 开发文档与第三方转述。 |
| Microsoft AI | Official | Global | [Website](https://microsoft.ai/)；[News](https://microsoft.ai/news/)；[AI Docs](https://learn.microsoft.com/ai/)；[GitHub](https://github.com/microsoft)；[Hugging Face](https://huggingface.co/microsoft) | P0 | Copilot、模型、AI 平台、企业生态 | High | Yes | Agent / AI Coding / Multimodal / Business / Ecosystem | 产品事实应优先引用对应官方文档。 |
| Meta AI | Official | Global | [Website](https://ai.meta.com/)；[Blog](https://ai.meta.com/blog/)；[GitHub](https://github.com/facebookresearch)；[Hugging Face](https://huggingface.co/meta-llama) | P0 | Llama、开源模型、研究、多模态 | High | Yes | Multimodal / Agent / Business / Ecosystem | 模型许可与权重条件必须回溯原始许可。 |
| xAI | Official | Global | [Website](https://x.ai/)；[News](https://x.ai/news)；[Docs](https://docs.x.ai/)；[GitHub](https://github.com/xai-org) | P0 | Grok、API、模型与公司发布 | High | Yes | Agent / Multimodal / Business / Ecosystem | X 上非 xAI 官方账号的讨论不属本条目。 |
| NVIDIA | Official | Global | [Website](https://www.nvidia.com/)；[AI Blog](https://blogs.nvidia.com/blog/category/generative-ai/)；[Docs](https://docs.nvidia.com/)；[GitHub](https://github.com/NVIDIA)；[Hugging Face](https://huggingface.co/nvidia) | P0 | 算力、推理、模型、具身智能、基础设施 | High | Yes | Runtime Core / Multimodal / Agent / Business / Ecosystem | 性能宣称需区分官方测试与独立评测。 |
| Mistral AI | Official | Global | [Website](https://mistral.ai/)；[News](https://mistral.ai/news)；[Docs](https://docs.mistral.ai/)；[GitHub](https://github.com/mistralai)；[Hugging Face](https://huggingface.co/mistralai) | P0 | 模型、API、开源生态、Agent | High | Yes | Agent / AI Coding / Multimodal / Business / Ecosystem | 开放权重与商业 API 应分开记录。 |
| Hugging Face | Official | Global | [Website](https://huggingface.co/)；[Blog](https://huggingface.co/blog)；[Docs](https://huggingface.co/docs)；[GitHub](https://github.com/huggingface) | P0 | 平台发布、开源工具、模型生态 | High | Yes | Multimodal / Agent / AI Coding / Business / Ecosystem | 只对 Hugging Face 自身平台发布为 P0；第三方模型卡按发布者重新定级。 |

### China

| Source | Type | Region | Platform / URL | Priority | Usage | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | Official | China | [Website](https://www.deepseek.com/)；[Docs](https://api-docs.deepseek.com/)；[GitHub](https://github.com/deepseek-ai)；[Hugging Face](https://huggingface.co/deepseek-ai) | P0 | 模型、API、开源、研究 | High | Yes | Agent / AI Coding / Multimodal / Business / Ecosystem | 仅登记公开入口，不包含账号或 API 凭证。 |
| 阿里 Qwen | Official | China | [Website](https://qwen.ai/)；[Blog](https://qwenlm.github.io/blog/)；[Docs](https://qwen.readthedocs.io/)；[GitHub](https://github.com/QwenLM)；[Hugging Face](https://huggingface.co/Qwen) | P0 | Qwen 模型、多模态、语音、AI Coding | High | Yes | Voice / STS / Multimodal / Agent / AI Coding / Business / Ecosystem | 云产品、开源仓库与社区讨论分开定级。 |
| 字节 Seed / 豆包 | Official | China | [Seed](https://seed.bytedance.com/)；[Seed News](https://seed.bytedance.com/en/blog)；[Doubao](https://www.doubao.com/)；[GitHub](https://github.com/ByteDance-Seed)；[Hugging Face](https://huggingface.co/ByteDance-Seed) | P0 | 模型、语音、多模态、Agent、产品 | High | Yes | Voice / STS / Multimodal / Agent / AI Coding / Business / Ecosystem | Seed 研究发布与豆包产品发布应保留各自原始来源。 |
| 智谱 GLM / Z.ai | Official | China | [Website](https://z.ai/)；[Docs](https://docs.z.ai/)；[GitHub](https://github.com/zai-org)；[Hugging Face](https://huggingface.co/zai-org) | P0 | GLM 模型、API、Agent、语音 | High | Yes | Voice / STS / Multimodal / Agent / AI Coding / Business / Ecosystem | 历史 THUDM 仓库可作追溯入口，当前发布优先核验 Z.ai 官方入口。 |
| Moonshot / Kimi | Official | China | [Moonshot](https://www.moonshot.cn/)；[Kimi](https://www.kimi.com/)；[Open Platform](https://platform.kimi.ai/)；[GitHub](https://github.com/MoonshotAI)；[Hugging Face](https://huggingface.co/moonshotai) | P0 | Kimi、模型、API、Agent、产品 | High | Yes | Agent / AI Coding / Multimodal / Business / Ecosystem | 区分公司官方、开发平台与用户社区内容。 |
| MiniMax | Official | China | [Website](https://www.minimaxi.com/)；[Global](https://www.minimax.io/)；[Docs](https://platform.minimaxi.com/document)；[GitHub](https://github.com/MiniMax-AI)；[Hugging Face](https://huggingface.co/MiniMaxAI) | P0 | 模型、语音、视频、多模态、Agent | High | Yes | Voice / STS / Multimodal / Agent / Business / Ecosystem | 国内与海外入口可不同，不绕过区域或访问限制。 |
| 腾讯混元 | Official | China | [Website](https://hunyuan.tencent.com/)；[Docs](https://cloud.tencent.com/document/product/1729)；[GitHub](https://github.com/Tencent-Hunyuan) | P0 | 模型、API、多模态、腾讯生态 | High | Yes | Multimodal / Agent / Business / Ecosystem | 云文档与开源仓库均需保留原始版本信息。 |
| 百度文心 | Official | China | [Wenxin](https://yiyan.baidu.com/)；[Qianfan](https://qianfan.cloud.baidu.com/)；[Docs](https://cloud.baidu.com/doc/WENXINWORKSHOP/)；[GitHub](https://github.com/PaddlePaddle) | P0 | 文心模型、千帆平台、多模态、开源生态 | High | Yes | Voice / STS / Multimodal / Agent / Business / Ecosystem | PaddlePaddle 为关联官方生态，不等同于所有文心产品发布。 |
| 华为盘古 | Official | China | [Website](https://www.huaweicloud.com/product/pangu.html)；[Docs](https://support.huaweicloud.com/pangu/)；[GitHub](https://github.com/HuaweiCloudDeveloper) | P0 | 盘古模型、行业 AI、基础设施 | High | Yes | Runtime Core / Multimodal / Agent / Business / Ecosystem | 仅使用公开可访问的华为云入口。 |
| 其他重要 AI 公司（准入位） | Official | China | 登记时核验官网、Newsroom、Docs、GitHub 与 Hugging Face | P0 | 新公司或重要发布的结构化纳入 | High | Conditional | 按实际内容选择 | 未完成官方身份与 URL 核验前不得激活为 P0 事实来源。 |

---

## 核心人物来源（People）

### 人物监控类别

- 创始人。
- 研究负责人。
- 产品负责人。
- 工程负责人。
- 开发者关系负责人。
- 重要研究员。

| Source | Type | Region | Platform / URL | Priority | Usage | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI 核心人员集合 | Person | Global | [OpenAI Forum](https://forum.openai.com/)；经官方身份核验的个人公开账号 | P1 | 模型、Codex、产品与工程早期信号 | Medium | Conditional | Agent / AI Coding / Multimodal / Business / Ecosystem | 只登记可核验身份的人物；个人观点不自动代表 OpenAI。 |
| Anthropic 核心人员集合 | Person | Global | [Research](https://www.anthropic.com/research)；经官方身份核验的个人公开账号 | P1 | Claude、安全研究、Agent、AI Coding 信号 | Medium | Conditional | Agent / AI Coding / Business / Ecosystem | 需回溯 Anthropic 官方发布确认产品事实。 |
| Google DeepMind / Gemini 核心人员集合 | Person | Global | [People](https://deepmind.google/about/)；经官方身份核验的个人公开账号 | P1 | 研究、Gemini、多模态与产品信号 | Medium | Conditional | Multimodal / Agent / Voice / STS / Business / Ecosystem | 个人预告与正式发布分开标记。 |
| xAI 核心人员集合 | Person | Global | [Company](https://x.ai/company)；经官方身份核验的个人公开账号 | P1 | Grok、模型、产品与公司信号 | Medium | Conditional | Agent / Multimodal / Business / Ecosystem | 不因 X 账号影响力自动提升为事实。 |
| Thibault “Tibo” Sottiaux | Person | Global | [OpenAI Forum](https://forum.openai.com/public/events/codex-is-for-everyone-why-codex-matters-beyond-code-fa40puy7wi)；[X](https://x.com/thsottiaux)；[GitHub](https://github.com/tibo-openai) | P1 | Codex 产品、工程与运行信号 | High | Conditional | Agent / AI Coding / Business / Ecosystem | OpenAI 公开页面确认其 Codex 相关身份；个人动态仍须按信号处理。 |
| 中国重点 AI 公司核心人员集合 | Person | China | 经公司官网、官方认证账号或公开演讲页面核验的个人入口 | P1 | 国内模型、产品、研究和生态早期信号 | Medium | Conditional | Voice / STS / Multimodal / Agent / AI Coding / Business / Ecosystem | 覆盖 DeepSeek、Qwen、Seed、GLM、Kimi、MiniMax、混元、文心、盘古等；每个人物必须单独核验。 |

人物来源用于发现信号，不代表其观点、预告或转发内容自动成为事实。

---

## 技术社区来源（Community）

| Source | Type | Region | Platform / URL | Priority | Discovery Value | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| X | Community | Global | [X](https://x.com/) | P3 | High | Low | No | Agent / AI Coding / Business / Ecosystem | 经身份核验的核心人物账号应单独登记为 Person / P1。 |
| Reddit | Community | Global | [Reddit](https://www.reddit.com/)；[r/MachineLearning](https://www.reddit.com/r/MachineLearning/) | P3 | High | Low | No | Agent / AI Coding / Multimodal / Business / Ecosystem | 适合发现使用反馈、漏洞线索和趋势，不单独证实事实。 |
| Hacker News | Community | Global | [Hacker News](https://news.ycombinator.com/) | P3 | High | Medium | No | Agent / AI Coding / Business / Ecosystem | 评论与外链必须分开评估。 |
| GitHub Trending | Community | Global | [GitHub Trending](https://github.com/trending) | P1 | High | Medium | Conditional | Runtime Core / Agent / AI Coding / Multimodal / Ecosystem | 趋势可证明仓库活跃信号，不能证明性能或产品宣称。 |
| Hugging Face Community | Community | Global | [Hugging Face](https://huggingface.co/) | P1 | High | Medium | Conditional | Voice / STS / Multimodal / Agent / AI Coding / Ecosystem | 官方组织页可单独登记为 P0；其他用户内容不自动成为事实。 |
| arXiv | Community | Global | [arXiv](https://arxiv.org/) | P1 | High | Medium | Conditional | Runtime Core / ECCS / Voice / STS / Multimodal / Agent / AI Coding | 可确认论文已公开，但预印本的研究结论不等同于已复现事实。 |
| TikTok | Community | Global | [TikTok](https://www.tiktok.com/) | P3 | High | Low | No | Voice / STS / Multimodal / Agent / Business / Ecosystem | 用于发现短视频平台用户趋势，不单独作为事实依据。 |
| 微博 | Community | China | [微博](https://weibo.com/) | P3 | High | Low | No | Agent / AI Coding / Multimodal / Business / Ecosystem | 官方认证账号应按 Official 或 Person 单独登记。 |
| 知乎 | Community | China | [知乎](https://www.zhihu.com/) | P3 | Medium | Low | No | Agent / AI Coding / Multimodal / Business / Ecosystem | 专业回答可作为线索，仍需回溯一手来源。 |
| B站 | Community | China | [哔哩哔哩](https://www.bilibili.com/) | P3 | High | Low | No | Voice / STS / Multimodal / Agent / AI Coding / Ecosystem | 适合发现演示、测评和用户反馈。 |
| 抖音 | Community | China | [抖音](https://www.douyin.com/) | P3 | High | Low | No | Voice / STS / Multimodal / Business / Ecosystem | 短视频内容默认只作趋势信号。 |
| 小红书 | Community | China | [小红书](https://www.xiaohongshu.com/) | P3 | High | Low | No | Aftelle / Digital Resident / Voice / STS / Multimodal / Business / Ecosystem | 适合发现用户体验和消费趋势。 |
| 微信公众号 | Community | China | 公开可访问的文章页；具体账号登记时核验 | P3 | High | Low | No | Agent / AI Coding / Multimodal / Business / Ecosystem | 已核验的公司官方公众号可单独定级；不绕过登录或访问限制。 |

---

## 媒体来源（Media）

| Source | Type | Region | Platform / URL | Priority | Usage | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| The Batch | Media | Global | [The Batch](https://www.deeplearning.ai/the-batch/) | P2 | AI 专业新闻与研究摘要 | Medium | Conditional | Multimodal / Agent / AI Coding / Business / Ecosystem | 重要结论回溯论文或官方发布。 |
| MIT Technology Review AI | Media | Global | [Artificial Intelligence](https://www.technologyreview.com/topic/artificial-intelligence/) | P2 | 科技媒体报道与深度分析 | Medium | Conditional | ECCS / Multimodal / Agent / Business / Ecosystem | 付费内容只使用合法可访问部分。 |
| TechCrunch AI | Media | Global | [Artificial Intelligence](https://techcrunch.com/category/artificial-intelligence/) | P2 | 产品、公司、融资与生态新闻 | Medium | Conditional | Agent / AI Coding / Business / Ecosystem | 公司数据与产品宣称需交叉核验。 |
| Stanford AI Index | Media | Global | [AI Index](https://aiindex.stanford.edu/report/) | P2 | 行业数据、趋势与年度分析 | High | Conditional | Business / Ecosystem / Multimodal / Agent | 引用时保留报告版本、年份和原始数据边界。 |
| 机器之心 | Media | China | [机器之心](https://www.jiqizhixin.com/) | P2 | AI 专业媒体、论文、产品与行业信息 | Medium | Conditional | Multimodal / Agent / AI Coding / Business / Ecosystem | 需回溯原始论文、仓库或官方公告。 |
| 量子位 | Media | China | [量子位](https://www.qbitai.com/) | P2 | AI 产品、研究、公司与趋势 | Medium | Conditional | Multimodal / Agent / AI Coding / Business / Ecosystem | 标题性结论不能替代原始证据。 |
| InfoQ AI | Media | China | [InfoQ](https://www.infoq.cn/topic/AI) | P2 | 工程、架构、AI Coding 与产品采访 | Medium | Conditional | Runtime Core / Agent / AI Coding / Business / Ecosystem | 采访中的个人判断与公司事实分开标记。 |
| 36氪 | Media | China | [36氪](https://36kr.com/) | P2 | 商业、融资、竞争与生态信号 | Medium | Conditional | Business / Ecosystem | 融资、估值和未官宣交易不得直接标记为 Confirmed。 |
| 行业分析机构公开报告 | Media | Global | 合法公开的报告页、摘要或数据集；具体机构按条目登记 | P2 | 市场、竞争、投资与生态分析 | Medium | Conditional | Business / Ecosystem | 禁止绕过付费墙；只使用已授权或公开部分。 |

---

## Eterna 关联分类

每个来源至少标记一个下列标签，支持后续价值分析：

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

标签表示可能的研究关联，不表示来源内容已改变 Eterna 路线、产品定义或任何 `FROZEN` 文档。

---

## 合规要求

以下规则为硬约束：

- 只使用公开、合法来源。
- 不绕过登录、验证码或访问限制。
- 不使用私有 API。
- 不逆向平台接口、签名算法、设备指纹或其他访问控制机制。
- 不保存 Cookie、Token、Session 或其他账号凭证。
- 不将未确认消息、人物观点、媒体转述或社区讨论当作已确认事实。
- 来源权限不足、入口失效或只能通过绕过控制取得时，必须放弃该入口或使用合法替代方案。

Source Registry 中存在某来源，不等于获得其自动采集、批量下载、再发布或商业使用授权。

---

## Stage 1.2 明确不做

- 不开发爬虫、采集器或调度器。
- 不实现或配置 RSSHub。
- 不接入任何 API。
- 不创建 GitHub Actions 或其他自动化。
- 不配置平台账号、鉴权、Cookie、Token 或 Session。
- 不定义 Stage 1.3 采集层的技术方案。
- 不根据来源清单自动修改 Eterna 正式定义或研究结论。

---

## Stage 1.2 节点验收标准

Stage 1.2 仅在以下条件全部满足时通过：

- Official、Person、Community、Media 四类来源体系已建立。
- P0–P3 优先级、可信度与事实引用边界已统一定义。
- 来源字段、初始清单与 Eterna 关联标签已记录。
- 人物、媒体和社区来源不会被自动视为事实。
- 公开、合法、不绕过访问控制的合规边界已写入。
- 本节点未新增任何采集、API、RSSHub 或自动化实现。
- 本节点未修改 Stage 1.1 或任何 Eterna `FROZEN` 上位文档，也未开始 Stage 1.3。
