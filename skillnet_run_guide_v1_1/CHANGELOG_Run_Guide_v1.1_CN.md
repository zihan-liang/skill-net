# SkillNet Run Guide v1.1 修改说明

本版基于 Run Guide v1.0 修订，重点冻结规模实验和父 Skill 独立扩展实验。

## 主要修改

1. E1 固定任务由 `GT01 / GT04 / GT13 / GT15 / GT20` 改为：
   `GT01 / GT04 / GT13 / GT15 / GT16`。
2. GT20 移回 S2 No-Tool 专门分析，不再占用规模实验名额。
3. 10-Skill 集合删除 `finance-budget-check`，加入 `procurement-supplier-selection`。
4. 重新核对 10-Skill 集合：覆盖五条任务的全部 required Skills、硬顺序，以及 GT16 的两个被阻断后续 Skill。
5. 30-Skill 集合同步调整，满足 `10 ⊂ 30 ⊂ 46`。
6. Configuration C 冻结为：Codex 直接读取 Skill 文件与 `skill_relations.json`，自行路由；不使用 Python planner。
7. 增加 C 在 10/30/46 条件下的闭合子图裁剪规则和实际验证结果。
8. 新增 S3 父 Skill 独立扩展实验：同时提供父 Skills 与原子 Skills，测试父流程识别、展开、分支与阻断，不要求重跑 E0/E1。
9. 更新实验运行量、指标实现状态、真实运行流程和待办清单。

## 配套验证结果

- 10-Skill：10 个 Skills，6 条 prerequisite，2 条 conflict，0 条 mutex，1 条 enhances，0 个清单外引用。
- 30-Skill：30 个 Skills，25 条 prerequisite，7 条 conflict，0 条 mutex，4 条 enhances，0 个清单外引用。
- 46-Skill：46 个 Skills，53 条 prerequisite，13 条 conflict，4 条 mutex，13 条 enhances，0 个清单外引用。
