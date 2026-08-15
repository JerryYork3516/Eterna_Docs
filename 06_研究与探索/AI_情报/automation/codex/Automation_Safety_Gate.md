# Codex AI Intelligence · Automation Safety Gate · Stage 1.12 A10 · v0.1

内部版本：`v0.1`

文档性质：Codex Automation 无人值守安全门禁

状态：`ACTIVE`

文档更新时间：`2026-08-15 21:07`（Asia/Shanghai）

> 本文件记录 Stage 1.12 A10 两条真实 Codex Automation 的运行模式与副作用门禁。
> 当前只批准自动研究与分析，不批准仓库写入、Git、Gmail、Secret 或其他外部执行。

---

## 当前门禁

```text
AUTOMATION_MAIN_WRITE_GATE = NOT READY
```

### UNATTENDED_OBSERVE

Stage 1.12 A10 当前唯一允许的无人值守模式。

允许：

- 自动触发对应 Region 的 Research；
- 使用公开、合法、已准入来源进行 Evidence Verification；
- 执行 Exact / Near / Same Event 判断与确定性 Event Anchor；
- 判断 Status、Confidence、Importance 并生成 Eterna Value Extraction；
- 返回 would-be report 与验证结果，供用户 review。

禁止：

- 修改 repository 中的任何文件；
- 写入 `reports/**`、`automation/state/**` 或其他路径；
- 执行 `git add`、commit、push 或其他 Git 写操作；
- 发送 Gmail 或创建 Email Delivery 状态；
- 修改 `FROZEN`、INDEX、CHANGELOG、配置或规则；
- 创建 Secret、OpenAI API / `LLMProvider`、GitHub Actions 或其他 scheduler；
- 因来源、日期、证据或治理条件不足而降低安全标准。

### UNATTENDED_WRITE

未来候选模式，当前未批准、未实现、未启用。

只有后续独立节点完成写入路径、幂等、并发、Git 身份、失败恢复、最小权限和安全验收，并明确将 `AUTOMATION_MAIN_WRITE_GATE` 改为可写状态后，Automation 才能进入该模式。A10 的创建成功、Observe 输出或人工 review 均不构成隐式批准。

---

## Automation 登记

| Name | Region | Schedule | Model / Reasoning | Mode | Creation Status |
| --- | --- | --- | --- | --- | --- |
| Eterna Global AI Intelligence | `Global` | 每日 `08:00 Asia/Shanghai` | `gpt-5.6-luna` / `high` | `UNATTENDED_OBSERVE` | `CREATED / ACTIVE` |
| Eterna China AI Intelligence | `China` | 每日 `20:00 Asia/Shanghai` | `gpt-5.6-luna` / `high` | `UNATTENDED_OBSERVE` | `CREATED / ACTIVE` |

- 两条任务均绑定本地 Eterna_Docs 项目，使用 Codex 本机 `Asia/Shanghai` 墙钟时间，不做 UTC 伪转换。
- Global 只读取 Global Task 与 Global sources；China 只读取 China Task 与 China sources。
- 两条任务均明确禁止 repository、Git 与 Gmail 副作用，并要求治理冲突、可靠 `event_date` 缺失或关键条件不足时 fail closed。
- 当前产品 Automation 管理工具未提供 Run now / Test 调用入口；A10 未模拟测试运行。

---

## Observe Run 输出合同

每次运行至少返回：

- Region、Actual Started At、Report Date 与 Coverage Window；
- Research：`PASS / PARTIAL / FAIL`；
- Event Count 与 Source Coverage / Gaps；
- Candidate Events：Event、deterministic Event Anchor、Status、Confidence、Importance 与 Evidence；
- Eterna Value Extraction；
- Would-be Report Path 与 Validation Result；
- `Repository Mutation = NOT_ATTEMPTED`；
- `Git = NOT_ATTEMPTED`；
- `Gmail = NOT_ATTEMPTED`；
- `AUTOMATION_MAIN_WRITE_GATE = NOT READY`。

输出只供 review，不是正式日报归档、邮件投递、Eterna 决策或上位文档变更。

---

## 安全结论

- A10 只验证“自动回来研究”，不验证自动写仓库。
- Automation 不获得 FROZEN、报告、状态、Git、Gmail 或 Secret 写权限。
- 不创建 GitHub Actions、系统 cron、launchd、daemon 或其他替代 scheduler。
- 不修改 macOS 电源设置，不开始 Stage 1.12 A11。
