SkillNet Gold Tasks + Deterministic Evaluation Package V4
版本：v4.0
日期：2026-07-28

一、本版核心变化

1. 删除Graph Validity Rate及所有graph_valid输出字段。
2. 删除company_skill_relations_v1.json和整个graph目录。
3. Python评估器不再接受--relations参数。
4. Gold Standard内置简单Skill/部门目录，用于名称和部门合法性检查，但不包含全局关系图。
5. 删除active_prerequisite_ids、active_hard_relation_ids、active_conditions等图验证字段。
6. hard_order_constraints改为完全自包含的任务级强制偏序。
7. 增加task_constraints，直接保存特殊冲突和互斥规则。
8. Constraint Violation Rate更名为Gold Constraint Violation Rate。
9. 修正GT08和GT10：技术验收路线明确禁止同时调用“业务验收”。

二、目录

01_Codex_Test_Prompts_21_V4.txt
  给被测试Codex读取的21条任务与固定输出格式。

02_Gold_Standard_21_V4.json
  自包含Gold答案和评价所需目录、偏序及任务级约束。

03_Gold_Tasks_Review_21_V4.md
  团队人工审核版。

04_Task_Coverage_Matrix_V4.csv
  任务类型、部门、关系与难度覆盖矩阵。

05_Evaluation_Design_CN.md
  中文评价设计说明。

evaluation/evaluate_skillnet.py
  Gold-only确定性评价器。

evaluation/prediction_schema.json
  Codex固定JSON输出Schema。

evaluation/predictions_template.jsonl
  21条输出模板。

predictions/A|B|C/run_01/
  保存各Configuration输出。

results/
  保存评分结果。

三、实验隔离

A、B、C读取各自允许的Skill组织文件和同一批测试Prompt。
Gold和evaluation文件不能提供给被测试Codex。
Configuration C的图实现是路由方法的一部分，但不进入评价器。

三组固定定义：

A（flat-skills）：只提供相同的46个原子Skills，不提供部门分组文件或关系图。
B（department-grouped-skills）：提供相同的46个原子Skills和department_groups.json，不提供关系图。
C（graph-assisted-skills）：提供相同的46个原子Skills和skill_relations.json；Graph只作为建议知识，由Codex自行选路，不执行硬路由。

所有机器读取和评分的Skill标识均使用SKILL.md YAML中的英文name。中文只用于业务Prompt、标题和人工说明。

四、使用顺序

1. 团队审核03_Gold_Tasks_Review_21_V4.md。
2. 运行validate-package，确认valid=true。
3. 运行A、B、C并保存固定JSON。
4. 分别执行evaluate。
5. 多次运行后执行aggregate。
6. 查看主指标、失败分析和人工复核队列。

五、运行Codex实验

三组使用完全相同的模型和设置，每题创建独立ephemeral session：

python evaluation/run_experiments.py \
  --configuration ALL \
  --run-id 1 \
  --model gpt-5.6-sol \
  --reasoning-effort medium \
  --max-workers 3
