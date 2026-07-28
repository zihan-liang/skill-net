# SkillNet routing evaluation: Configuration C

Read `skill_relations.json` before deciding which enterprise Skills are needed and in what order. Treat `contains`, `prerequisite`, `conflict`, `mutex`, and `enhances` as advisory graph knowledge. Activate only edges relevant to the task's scope, current state, conditions, and stated goal; do not mechanically execute every reachable Skill.

This is a routing evaluation, not a hard-routed workflow. Do not execute the business workflow, modify files, or invent completed approvals or outcomes. Select the applicable route yourself and return only the JSON object requested by the task.
