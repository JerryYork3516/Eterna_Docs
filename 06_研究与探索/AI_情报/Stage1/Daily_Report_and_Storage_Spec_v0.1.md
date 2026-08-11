# AI 情报自动化系统 · Daily Report and Storage Spec · Stage 1.8 · v0.1

内部版本：`v0.1`

文档性质：AI 情报日报格式与 Docs 存储规范

状态：`FROZEN`

文档更新时间：`2026-08-11 21:57`（Asia/Shanghai）

> 本文件只冻结 Global / China AI 情报日报的 Markdown 格式、命名、归档和修订规则。
> 本文件属于研究/工程规划，不构成 Eterna 正式产品定义、架构决策、路线承诺或自动执行授权。

---

## 1. 适用范围与继承边界

- 本规范位于 `06_研究与探索/AI_情报`，继承 Stage 1.1–1.7 已冻结的目标、来源、采集边界、数据契约、聚类、分析和 Eterna 价值提取规则。
- 本节点只定义最终日报的可读表示与存储边界，不改变 `IntelligenceReport` 数据对象及既有字段语义。
- Global 与 China 是两条独立日报链；本节点不进行跨区域事件合并或联合报告。
- 日报是研究历史记录，不得作为 Eterna 正式定义、ADR、施工任务、路线变更或 `FROZEN` 文档更新指令。

---

## 2. 存储目录与文件命名

### 2.1 目标结构

```text
06_研究与探索/AI_情报/
├── Stage1/
├── reports/
│   ├── global/YYYY/MM/
│   └── china/YYYY/MM/
└── README.md
```

- Stage 1.8 只冻结以上目标结构，不批量创建未来月份目录、`README.md` 或任何日报文件。
- `reports/` 目录应在后续实现首次写入有效日报时按需创建；不得使用空目录或无意义占位文件表示结构。
- `YYYY/MM` 必须由日报的 `report_date` 推导，不得由采集时间或提交时间推导。

### 2.2 规范路径

- Global：`reports/global/YYYY/MM/YYYY-MM-DD_Global_AI_Intelligence.md`
- China：`reports/china/YYYY/MM/YYYY-MM-DD_China_AI_Intelligence.md`

每个 Region、每个业务日期只能有一份正式日报。不得通过随机后缀或重复文件规避该唯一性约束。

---

## 3. 时间规范

每份日报必须明确记录：

- `report_date`：报告业务日期，按声明的 `Report Timezone` 解释。
- `coverage_started_at`：覆盖窗口的实际开始时间。
- `coverage_ended_at`：覆盖窗口的实际结束时间。
- `report_generated_at`：本次报告实际生成时间。

所有时间必须使用含 UTC 偏移量的 ISO 8601 表达，或明确使用 UTC 的 `Z` 表达。不得把来源发布时间、采集时间或报告生成时间相互替代。

Global 报告面向早间任务，China 报告面向晚间任务；本规范不定义具体时刻、时区调度、cron 或重试周期。

---

## 4. 文档头部格式

Global 标题：

```markdown
# Global AI Intelligence · Daily Report · YYYY-MM-DD
```

China 标题：

```markdown
# China AI Intelligence · Daily Report · YYYY-MM-DD
```

标题后必须提供以下元数据：

```markdown
Report ID：`<report_id>`

Report Date：`YYYY-MM-DD`

Region：`Global | China`

Report Timezone：`<IANA timezone>`

Coverage：`<coverage_started_at> → <coverage_ended_at>`

Generated At：`<report_generated_at>`

Status：`Generated | Partial | No valid report | Failed`

Revision：`rN`
```

`Revision` 是文档修订标记，不新增或改变 Stage 1.4 的概念数据字段。

### 4.1 报告状态

- `Generated`：完成有效日报；不表示来源覆盖率为 100%。
- `Partial`：报告可用，但存在重大来源或处理缺口；必须在“来源覆盖情况”中列出缺口与影响。
- `No valid report`：流程完成，但没有事件达到日报准入标准；使用空日报规则。
- `Failed`：未形成可分析日报；不得伪造摘要、事件或覆盖情况。

来源失败时不得标记为完整覆盖。`Partial` 或 `Failed` 后续修正仍必须遵守修订规则。

---

## 5. 日报固定结构

每份正式日报按以下顺序组织：

1. `## 今日核心摘要`
2. `## 重要事件`
3. `## 社区与早期信号`
4. `## 来源覆盖情况`
5. `## Eterna 价值提取`
6. `## Revision History`

### 5.1 今日核心摘要

- 只概括本报告已收录的 IntelligenceEvent，不引入正文之外的新事实。
- 优先覆盖高重要度且有充分 Evidence 的事件。
- 传闻、信号或社区趋势必须保留其信息状态，不得改写为已确认事实。

### 5.2 重要事件

每个事件使用以下格式：

```markdown
### <标准事件标题>

- What happened：<发生了什么>
- Status：Confirmed | High-confidence signal | Unconfirmed | Community trend
- Confidence：<Stage 1.6 定义的判断结果>
- Importance：<Stage 1.6 定义的判断结果>
- Why it matters：<与现实 AI 事件相关的重要性说明>
- Evidence / Sources：
  - Primary：<来源名称> — <原始公开 URL>
  - Supplement：<来源名称> — <原始公开 URL>
  - Contradicts：<来源名称> — <原始公开 URL>
```

- 一手或最权威来源优先；补充与冲突 Evidence 分开标识并保留原始 URL。
- Near Duplicate 不在正文中重复展开；其 Evidence 仍保留在事件追溯链中。
- `Unconfirmed`、`High-confidence signal` 与 `Community trend` 必须在 `Status` 中显式可见，正文措辞也必须保持不确定性。
- 重要传闻可以进入“重要事件”，但不得因此自动提升为 `Confirmed`。

### 5.3 社区与早期信号

- 收录达到 Stage 1.6 准入标准、但以社区趋势或早期信号为主的事件。
- 每项仍使用与“重要事件”相同的事件字段，不得省略 Status、Confidence 或 Evidence / Sources。
- 同一 IntelligenceEvent 不得同时在两个章节重复出现。

### 5.4 来源覆盖情况

至少按 P0–P3 记录：

- 本窗口计划覆盖范围；
- 成功取得有效结果的来源数；
- 不可用来源数；
- 已知覆盖缺口及其影响；
- 是否缺失关键 P0 来源。

覆盖统计只描述本窗口实际观察，不代表互联网或某个平台的全量覆盖。不得在缺少证据时声明“100% 覆盖”或等价表述。

### 5.5 Eterna 价值提取

必须沿用 Stage 1.7 的固定结构：

```markdown
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

每项判断必须保持 Evidence basis、分析推断与 Current-stage fit 可区分；“Eterna 今日主控判断”只是研究摘要，不是控制指令。

价值提取只能形成研究输入，不得自动修改 Eterna 正式路线、Stage、任务、ADR 或 `FROZEN` 文档。

---

## 6. 篇幅与空日报

- 日报应优先保证信息密度、来源追溯和状态清晰，不为凑长度收录低价值信息。
- 核心摘要保持简洁；事件说明覆盖必要事实、证据和重要性即可。
- 当没有事件达到准入标准时，Status 使用 `No valid report`，并在“今日核心摘要”写明：

> 本时间窗口无达到日报准入标准的重要新增事件。

- 空日报仍必须保留头部元数据、来源覆盖情况、Eterna 价值提取结论和 Revision History；不得伪造事件填充报告。

---

## 7. 重跑、修订与历史保留

- 首次正式提交前，重跑可以替换尚未发布的工作区草稿，但不得产生多个正式日报文件。
- 首次正式提交后，禁止静默覆盖。重大事实更正、官方澄清、来源撤回或关键 Evidence 更新时，保持规范文件名，递增 `Revision`，并在 `Revision History` 追加时间、原因和变更摘要。
- 历史修订通过文档内 Revision History 与 Git 历史共同保留；不得删除或伪造先前来源与状态。
- 日报应保留从 IntelligenceEvent 经 Evidence、CandidateItem、Source Registry 到原始公开 URL 的反向追溯能力。
- 已归档日报不得因生成时间变化而迁移到其他月份；归档位置始终由 `report_date` 决定。

---

## 8. GitHub、Obsidian 与仓库治理

- 使用稳定、可读的标准 Markdown；在 GitHub 与 Obsidian 中均不得依赖专有渲染能力才能理解正文。
- 正式日报应单独提交，或纳入边界明确的同批自动化提交；提交范围不得混入上位文档或治理规则变更。
- 后续日报自动化即使获准，也只能写入对应 `reports/**` 路径，绝不得修改 `Stage1/**`、根 `INDEX.md`、`CHANGELOG.md` 或任何 Eterna `FROZEN` 文档。
- 本规范只冻结写入边界，不设计 GitHub Actions、自动提交、权限或部署方案。

---

## 9. Global / China 隔离

- Global 报告只能包含 Global IntelligenceEvent；China 报告只能包含 China IntelligenceEvent。
- 两条链分别生成摘要、来源覆盖统计和 Eterna 价值提取。
- 同一现实事件即使被两个区域报道，也不得在 Stage 1.8 跨 Region 合并。
- 文件路径、Report ID、覆盖窗口和修订历史均保持独立。

---

## 10. 合规与安全硬约束

- 只展示通过公开、合法、授权方式取得的最小必要信息和来源引用。
- 不保存或展示 Cookie、Session、Token、API Key、账号密码或他人凭证。
- 不绕过登录、验证码、付费墙、Rate Limit、访问控制、安全验证或平台风控。
- 不调用未授权私有接口，不逆向平台访问控制机制。
- 来源不可访问或覆盖不足时如实标记，不伪造正文、来源或完整覆盖。
- 自动化失败不得触发绕过安全机制的降级策略。

---

## 11. 本节点明确不做

Stage 1.8 不做：

- 不创建真实 Global / China 日报；
- 不批量创建 `reports/` 目录、月份目录或 `README.md`；
- 不实现日报生成器、脚本、Prompt、模型调用或 Schema；
- 不创建数据库，不实现 Collector、分析或聚类；
- 不实现 Gmail、邮件模板、GitHub Actions、cron、定时任务或自动提交；
- 不修改 Stage 1.1–1.7 或 Eterna 上位 `FROZEN` 文档；
- 不开始 Stage 1.9。

---

## 12. Stage 1.8 验收标准

Stage 1.8 只有同时满足以下条件才可 PASS：

- Global / China 日报格式、路径和唯一文件命名已冻结；
- 时间、头部、状态与固定章节完整；
- Event、Evidence / Sources 和 Eterna 价值提取展示规则完整；
- `Confirmed`、`High-confidence signal`、`Unconfirmed`、`Community trend` 可明确区分；
- P0–P3 来源覆盖、重大缺口和关键 P0 缺失可被如实记录；
- 空日报、重跑、Revision History 和归档边界明确；
- Global / China 保持独立，端到端追溯性不被破坏；
- 合规与账号安全边界完整；
- 未进入任何代码、自动化或真实日报实现；
- 未修改任何 Eterna 上位 `FROZEN` 文档，未开始 Stage 1.9。
