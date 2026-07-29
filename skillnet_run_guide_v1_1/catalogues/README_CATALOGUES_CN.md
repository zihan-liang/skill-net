# SkillNet E0/E1 正式 A/B/C Catalogue

Source commit: `742e39d837484e5311e6663658bc7420c2a07a6b`

SHA-256 追踪：本目录所有正式输入与说明文件的 SHA-256 由 `catalogue_manifest.json` 集中记录；每份 Catalogue 还记录 `skill_cards_sha256`，C 另记录 `relations_sha256`。manifest 自身的 SHA-256 在本地交付说明中外部记录，以避免自引用。

## 为什么 `.agents/skills/` 只是 source

`.agents/skills/` 是 46 个原子 Skill 的权威源文件库。它包含分散的 Skill 文档、运行资产和元数据，允许扫描整个目录会让实验输入边界不固定，也难以证明 A/B/C 只改变组织结构。正式 Catalogue 把当前条件允许看到的 Skill Card 冻结在单个 JSON 中，因此可以校验规模、字段一致性、排序和关系暴露范围。

实验 Codex 不得再扫描整个 repo，也不得读取 `.agents/skills/`、Gold、evaluator、原始关系文件或其他规模/Configuration 的 Catalogue。每个实验 packet 一次只放当前 size/configuration 的一个 Catalogue 与当前任务 Prompt。

## A/B/C 分别给实验 Codex 看什么

- A（Flat）：一个按 `skill_id` 字母顺序排列的平铺 `skills` 数组；不含部门嵌套，不含显式关系。
- B（Department-grouped）：与 A 完全相同的 Skill Cards，按 5 个 canonical department IDs 分组；部门及组内 Skills 均按 ID 字母顺序。分组只表示归属，不暗示执行顺序。
- C（Graph-structured）：与 B 完全相同的部门结构和 Skill Cards，额外增加明确的 prerequisite、directional conflict、mutex、enhances 关系及其语义。

C 中的 department 是归属层，不是高层可执行 Skill，也不表示流程、展开或执行顺序。本 Catalogue 不含 S3 扩展实验所讨论的高层流程实体。

部门英文名和中文显示名严格采用 `SkillNet_Gold_Tasks_V4/skill_name_map.json` 的当前值（例如 `Business Agent` / `业务部门`），而不是根据结构示例另造 `Business` / `商务`。这项选择在 validation report 中显式记录。

`agents/openai.yaml` 仅用于交叉检查：其中 12 个 `display_name` 与 `SKILL.md` H1 在缩写大小写或连接词上不同，46 个 `short_description` 都是较短的界面摘要而非 frontmatter 原文。正式 Skill Card 按冻结规则使用 `SKILL.md` H1 和 frontmatter `description`；全部差异逐项记录在 validation report，不视为 canonical 冲突。

## E0 与 E1 使用路径

### E0：完整 46-Skill

- A：`skillnet_run_guide_v1_1/catalogues/size_46/A_flat_catalogue.json`
- B：`skillnet_run_guide_v1_1/catalogues/size_46/B_department_grouped_catalogue.json`
- C：`skillnet_run_guide_v1_1/catalogues/size_46/C_graph_structured_catalogue.json`

E0 对 GT01-GT21 使用以上 46-Skill Catalogue；每次运行只提供对应 Configuration 的一个文件。

### E1：规模 10/30/46

- size 10：`skillnet_run_guide_v1_1/catalogues/size_10/{A_flat_catalogue.json|B_department_grouped_catalogue.json|C_graph_structured_catalogue.json}`
- size 30：`skillnet_run_guide_v1_1/catalogues/size_30/{A_flat_catalogue.json|B_department_grouped_catalogue.json|C_graph_structured_catalogue.json}`
- size 46：复用 E0 的 size 46 三份 Catalogue。

E1 只运行 manifest 冻结的 GT01、GT04、GT13、GT15、GT16；本次工作不运行这些任务。

## 简短 diff summary

### A 与 B

- A 顶层是单个 `skills` 数组。
- B 用 5 个按 ID 排序的 `departments` 容器承载同一批 Skill Cards。
- B 不增加任何 prerequisite、conflict、mutex 或 enhances 信息。

### B 与 C

- C 的 `departments` 与 B 逐字节语义等价（相同顺序、相同 Skill Cards）。
- C 只增加 `relations`、`relation_semantics` 和关系内容 hash；不改变 Skill Card。
- `contains` 的归属语义已由相同的 department grouping 表达，不再暴露容易误解的结构字段。

### 三者相同的 Skill Card 示例

```json
{
  "skill_id": "finance-budget-check",
  "name_en": "Finance Budget Check",
  "display_name_zh": "预算检查",
  "description_en": "Use when a purchase or expense needs budget balance, funding source, budget account, approval threshold, and availability checks; not for creating the budget or approving the expense.",
  "description_zh": "核对预算余额、资金来源、预算科目、审批阈值和预算可用性；采购可调用，但归属财务，检查结果不等于批准支出。",
  "department_id": "finance-agent",
  "source_skill_md": ".agents/skills/finance-budget-check/SKILL.md"
}
```

### C relation normalization 示例

原始 directional conflict：

```json
{
  "skills": [
    "finance-budget-check",
    "procurement-purchase-order"
  ],
  "condition": "budget_not_approved"
}
```

正式 C 表达：

```json
{
  "gate_skill": "finance-budget-check",
  "blocked_skill": "procurement-purchase-order",
  "condition": "budget_not_approved"
}
```

字段表达更明确，但 gate、blocked endpoint 和 condition 均未改变。
