<!-- BEGIN ETERNA REPOSITORY COMPASS -->
## Eterna 仓库指南针
Eterna 采用多仓库管理。各仓库拥有明确且独立的职责。
| 仓库 | 定位 | 主要职责 |
|---|---|---|
| [Eterna_docs](https://github.com/JerryYork3516/Eterna_docs) | Eterna 权威文档与知识库 | 保存 Eterna 总体定义、数字居民定义、产品拓扑、跨系统边界、核心领域规范与长期治理文档 |
| [Eterna_studio](https://github.com/JerryYork3516/Eterna_studio) | Studio Legacy 仓库 | 保存现有 Studio 的代码、Canvas、Module Graph、DR Compiler、Runtime 链路与历史兼容实现；作为 Studio Next 重构、迁移和回归基线 |
| [Eterna_StudioNext](https://github.com/JerryYork3516/Eterna_StudioNext) | Studio Next 主工程仓库 | 承载 Studio Next 1.0 的规划、需求、产品设计、目标架构、核心契约、迁移方案、开发计划、源代码与测试 |
| [Eterna_aftelle](https://github.com/JerryYork3516/Eterna_aftelle) | 数字居民运行与陪伴应用 | 承载 Aftelle Apple 端应用、Runtime Core、数字居民加载、对话、语音、视觉表现、记忆与运行期交互 |
| [eterna-homepage](https://github.com/JerryYork3516/eterna-homepage) | Eterna 官方网站 | 承载 Eterna 品牌展示、公开项目介绍、产品入口与对外信息 |
### 仓库关系
```text
Eterna_docs
    ↓ 提供上位定义、核心领域规范与系统边界
Eterna_StudioNext
    ↓ 设计、编辑、验证、编译和发布数字居民
Eterna_aftelle
    ↓ 加载、运行和呈现数字居民
Eterna_studio
    ↓ 作为 Legacy 事实来源、迁移来源和回归基线
eterna-homepage
    ↓ 提供 Eterna 的公开展示与产品入口

权威边界

- Eterna 总体定义、数字居民上位定义和跨产品规则，以 Eterna_docs 的冻结文档为准。
- Studio Next 的需求、产品设计、目标架构、核心契约和正式实现，以 Eterna_StudioNext 为准。
- Studio Legacy 的现有实现事实，以 Eterna_studio 指定 Commit 的代码和可重复运行结果为准。
- Aftelle 的运行端实现、设备交互和 Runtime Core 行为，以 Eterna_aftelle 为准。
- Eterna 官方公开网站的实现和发布，以 eterna-homepage 为准。
- 本指南针只用于仓库导航，不替代各仓库中的正式权威文档。

<!-- END ETERNA REPOSITORY COMPASS -->
