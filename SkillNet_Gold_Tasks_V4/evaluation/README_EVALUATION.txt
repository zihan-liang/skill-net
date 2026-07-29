SkillNet Python Evaluation V4 — English/Bilingual

ENGLISH
=======

The evaluator uses only task-level Gold rules. It does not read a global relation
graph and does not compute any graph-validity metric.

Prediction fields:
- task_id
- use_skills
- selected_departments (canonical department IDs)
- skill_sequence (canonical Skill IDs)
- final_status
- blocked_by (canonical Skill IDs)
- route_choice
- reason

Validate:
  python evaluate_skillnet.py validate-package \
    --gold ../02_Gold_Standard_21_V4.json \
    --output ../results/package_validation_report.json

Evaluate:
  python evaluate_skillnet.py evaluate \
    --gold ../02_Gold_Standard_21_V4.json \
    --predictions ../predictions/A/run_01 \
    --configuration A --run-id 1 \
    --output-dir ../results/A_run_01

Aggregate:
  python evaluate_skillnet.py aggregate \
    --input-root ../results \
    --output-dir ../results/summary

Metrics:
- Functional Success Rate
- Clean Success Rate
- Skill Precision, Recall, and F1
- Required Order Accuracy
- Gold Constraint Violation Rate
- Department Precision, Recall, and F1
- No-Tool Accuracy
- Blocked-Flow Accuracy

中文
====

评价器只使用任务级 Gold 规则，不读取全局关系图，也不计算任何图有效性指标。
selected_departments 必须使用规范部门 ID；skill_sequence 与 blocked_by 必须使用
规范英文 Skill ID。命令与指标同上。
