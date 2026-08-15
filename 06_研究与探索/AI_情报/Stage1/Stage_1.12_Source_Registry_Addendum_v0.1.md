# AI 情报自动化系统 · Source Registry Addendum · Stage 1.12 · v0.1

内部版本：`v0.1`

文档性质：Stage 1.12 Personal MVP Source Registry 追加准入

状态：`FROZEN`

文档更新时间：`2026-08-15 16:50`（Asia/Shanghai）

> 本文件以追加方式为 Current Personal MVP 准入明确列出的来源。
> 本文件不修改 Stage 1.2 Source Registry 历史正文，不构成动态来源扩张、采集授权或 Eterna 正式产品定义。

---

## 权威关系

Current Personal MVP 的来源权威为：

```text
Source_Registry_v0.1.md
+
当前有效、明确批准的 Stage 1.12 Source Registry Addendum
```

- 本 Addendum 只新增下表明确列出的来源，不改变既有来源的 Type、Priority、Credibility、Fact Citation 或其他治理属性。
- 未列出的来源不会因被 Codex、搜索服务或外部内容发现而自动获得准入。
- 新来源仍须通过独立、显式的治理变更完成准入；日报任务不得动态修改 Base Registry 或 Addendum。
- 当前 A2 Python Registry Parser 可继续只消费 Base Registry；多 Registry 文件的 Production Route 支持不属于本节点。

---

## 追加官方来源（Official）

### Global

| Source | Type | Region | Platform / URL | Priority | Usage | Credibility | Fact Citation | Eterna Tags | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GitHub | Official | Global | [Platform](https://github.com/)；[Blog](https://github.blog/)；[Changelog](https://github.blog/changelog/) | P0 | GitHub Copilot、GitHub 产品、官方 Changelog 与 AI Coding 平台事实 | High | Yes | Agent / AI Coding / Business / Ecosystem | 只对 GitHub 自身产品、Changelog 和平台公告具有一手权威；第三方 GitHub repository 内容仍按实际发布主体单独判断。任意 `github.com/*` 路径不会自动成为 GitHub 官方事实。 |

`Fact Citation = Yes` 只适用于 GitHub 自身权威范围内的公开陈述。引用时仍须保留实际公开 URL、发布时间及 Evidence 关系，不得把 GitHub 承载的第三方仓库、Issue、Discussion、用户内容或外链声明提升为 GitHub 官方事实。

---

## 合规与边界

- 继续继承 Stage 1.1–1.12 已冻结的公开、合法、授权访问边界。
- 不绕过登录、验证码、Rate Limit、付费墙、风控或访问控制，不调用私有未授权接口。
- 不保存 Cookie、Session、Token、API Key 或账号凭证。
- 本 Addendum 只完成来源治理准入，不配置 Collector、API、Automation、GitHub Actions 或 Gmail。
- 未登记来源可用于 discovery，但不得直接成为带正式来源评级的 Evidence；必须先完成显式准入，或由已登记的合法来源完成核验。

---

## 冻结结论

- GitHub 自有 Platform、Blog 与 Changelog 作为 `Global / Official / P0 / High / Fact Citation Yes` 来源进入 Current Personal MVP。
- Base Source Registry 保持不变；本文件仅追加 GitHub 一项明确准入。
- `AUTOMATION_MAIN_WRITE_GATE = NOT READY`；本文件不授权无人值守写入或任何外部副作用。
