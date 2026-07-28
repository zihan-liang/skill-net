SkillNet Python Evaluation V4

一、核心变化

1. 本版本不读取relations.json，也不计算Graph Validity Rate。
2. 评分完全依据02_Gold_Standard_21_V4.json中的任务级规则。
3. hard_order_constraints保存必须满足的强制偏序，不比较完整序列完全相等。
4. task_constraints保存特殊冲突和互斥规则。
5. 原Constraint Violation Rate改名为Gold Constraint Violation Rate。

二、预测输出格式

每条Codex输出必须包含：
- task_id
- use_skills
- selected_departments
- skill_sequence
- final_status
- blocked_by
- route_choice
- reason

Skill名称必须使用对应SKILL.md YAML中的完整英文name。

三、运行Codex A/B/C实验

python run_experiments.py \
  --configuration ALL \
  --run-id 1 \
  --model gpt-5.6-sol \
  --reasoning-effort medium \
  --max-workers 3

四、正式运行前验证Benchmark

python evaluate_skillnet.py validate-package \
  --gold ../02_Gold_Standard_21_V4.json \
  --output ../results/package_validation_report.json

五、运行单次评估

python evaluate_skillnet.py evaluate \
  --gold ../02_Gold_Standard_21_V4.json \
  --predictions ../predictions/A/run_01 \
  --configuration A \
  --run-id 1 \
  --output-dir ../results/A_run_01

六、汇总A/B/C

python evaluate_skillnet.py aggregate \
  --input-root ../results \
  --output-dir ../results/summary

七、主要指标

- Functional Success Rate
- Clean Success Rate
- Skill Precision / Recall / F1
- Required Order Accuracy
- Gold Constraint Violation Rate
- Department F1
- No-Tool Accuracy
- Blocked-Flow Accuracy

八、Functional Success

正常任务要求：
- 输出格式、Tool判断和最终状态正确；
- 必要Skill完整；
- 强制偏序全部满足；
- 必要部门完整；
- 不违反任务级禁止、冲突、互斥、路线和初始状态规则。

Blocked任务要求正确停止、阻断来源正确，且不继续调用被禁止步骤。

九、人工复核

人工复核自动失败、使用别名、理由与路径可能矛盾，以及可能存在Gold歧义的案例。
