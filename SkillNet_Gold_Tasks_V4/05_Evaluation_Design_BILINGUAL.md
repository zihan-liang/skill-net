# SkillNet Evaluation Design V4 — English/Bilingual

## English

### 1. Objective

Compare configurations A, B, and C on the same 21 routing tasks without using an
LLM as a judge. Predictions are structured JSON and are scored deterministically
against task-level Gold rules.

### 2. Inputs and experiment isolation

Each tested Codex receives only the common prompt set and the Skill-organization
files allowed by its configuration. It must not receive the Gold Standard,
mapping report, evaluator, or validation fixtures. Configuration C may use the
repository's `skill_relations.json` as routing input, but the evaluator remains
independent of that file.

### 3. Canonical identifiers

All machine-readable Skill values are exact IDs from `main/.agents/skills`.
All machine-readable department values are exact parent IDs from
`main/skill_relations.json`. Chinese names are display-only metadata in
`skill_name_map.json`.

### 4. Gold semantics

- `required_skills`: necessary remaining Skills.
- `optional_skills`: accepted but unnecessary Skills.
- `forbidden_skills`: contextually prohibited canonical Skill IDs.
- `forbid_all_skills`: prohibits every Skill for a no-tool task.
- `hard_order_constraints`: mandatory partial orders only.
- `canonical_sequence`: one reviewable valid sequence, not an exact-match target.
- `initial_skill_states`: already completed or known Skill outcomes.
- `expected_blocked_by`: canonical IDs for the active blocking result.
- `task_constraints`: task-level conflict and mutex rules.

### 5. Metrics preserved

The design preserves Functional Success, Clean Success, Skill Precision, Skill
Recall, Skill F1, Required Order Accuracy, Department Precision/Recall/F1, Gold
Constraint Violation Rate, No-Tool Accuracy, and Blocked-Flow Accuracy.

Functional Success requires correct format, tool decision, status, all required
Skills, all mandatory partial orders, required departments, route choice, and no
task-level constraint violation. Clean Success additionally requires perfect
Skill and department precision and no duplicate Skill IDs.

### 6. Deterministic failures

The evaluator preserves failure tags for invalid JSON, missing fields, invalid
values, false activation/abstention, wrong status, wrong blocker or route,
conflict/mutex/forbidden violations, continuation after a block, repeated
completed Skills, missing required Skills, order violations, unknown Skills or
departments, missing departments, unnecessary Skills, extra departments, and
duplicate Skills.

### 7. Partial-order policy

Only explicit `hard_order_constraints` are mandatory. Independent Skills may be
interleaved or reordered. A valid alternative sequence is therefore accepted
when it contains all required Skills and satisfies every mandatory pair.

## 中文

### 1. 目标

在同一批 21 个路由任务上比较 A、B、C，不使用 LLM 评分。预测为结构化 JSON，
评价器依据任务级 Gold 规则进行确定性评分。

### 2. 输入与实验隔离

被测试 Codex 只能读取统一提示和当前配置允许的 Skill 组织文件，不得读取 Gold、
映射报告、评价器或验证样例。Configuration C 可以使用仓库的
`skill_relations.json` 进行路由，但评价器与该文件保持独立。

### 3. 规范标识符

所有机器可读 Skill 值都使用 `main/.agents/skills` 的精确 ID；所有机器可读部门值
都使用 `main/skill_relations.json` 的 parent ID。中文名称仅作为
`skill_name_map.json` 中的展示元数据。

### 4. Gold 语义

required_skills 是尚需执行的必要 Skill；optional_skills 是允许但非必要的 Skill；
forbidden_skills 是任务情境下禁止的规范 Skill ID；forbid_all_skills 用于 no-tool
任务；hard_order_constraints 只保存强制偏序；canonical_sequence 只是一个可行示例；
initial_skill_states 保存已完成或已知结果；expected_blocked_by 保存阻断来源；
task_constraints 保存任务级冲突和互斥规则。

### 5. 保留指标

保留 Functional Success、Clean Success、Skill Precision/Recall/F1、Required Order
Accuracy、Department Precision/Recall/F1、Gold Constraint Violation Rate、
No-Tool Accuracy 和 Blocked-Flow Accuracy。

### 6. 确定性失败检测

继续检测无效 JSON、缺字段、非法值、错误工具触发或放弃、错误状态、错误阻断来源、
错误路线、冲突/互斥/禁止 Skill、阻断后继续、重复已完成 Skill、缺失必要 Skill、
顺序错误、未知 Skill 或部门、缺失部门、不必要 Skill、额外部门和重复 Skill。

### 7. 偏序策略

只强制 hard_order_constraints 中明确列出的偏序。彼此独立的 Skill 可以交错或换序；
只要包含全部必要 Skill 并满足所有强制对，合法替代序列就应通过。
