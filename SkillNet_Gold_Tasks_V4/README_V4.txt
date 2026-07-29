SkillNet Gold Tasks V4 — English/Bilingual Edition
Version: v4.1-bilingual
Date: 2026-07-29

ENGLISH
=======

Purpose
-------
This package contains 21 deterministic routing tasks. All machine-readable Skill
and department values use exact canonical English IDs from main. Chinese remains
only as bilingual display metadata and documentation.

Canonical mapping
-----------------
skill_name_map.json is the central display mapping. It records each canonical
Skill ID, authoritative English title, Chinese display name, department ID,
English department name, Chinese department display name, and source in main.

Core files
----------
01_Codex_Test_Prompts_21_V4.txt
  Complete independent English prompt set followed by a complete Chinese version.
02_Gold_Standard_21_V4.json
  Bilingual task metadata with canonical English machine IDs.
03_Gold_Tasks_Review_21_V4.md
  Team review document in English and Chinese.
04_Task_Coverage_Matrix_V4.csv
  English CSV columns plus Chinese display columns.
05_Evaluation_Design_BILINGUAL.md
  Complete evaluation design in English and Chinese.
skill_name_map.json
  Single central Skill and department display mapping.
evaluation/evaluate_skillnet.py
  Deterministic Gold-only evaluator.
evaluation/prediction_schema.json
  Prediction schema constrained to canonical IDs.
evaluation/tests/test_evaluator.py
  Regression tests for required success and failure behavior.

Experiment isolation
--------------------
Configurations A, B, and C receive the same task prompts and only their allowed
Skill-organization inputs. The tested Codex must not receive Gold or evaluation
files. Configuration C may use main/skill_relations.json as a routing input, but
the evaluator never reads or requires that graph.

Evaluation workflow
-------------------
1. Review 03_Gold_Tasks_Review_21_V4.md and SKILL_NAME_MAPPING_REPORT.md.
2. Run validate-package.
3. Run each configuration and save canonical-ID predictions.
4. Run evaluate for each configuration/run.
5. Run aggregate across runs.
6. Review metrics, failure analysis, and the manual-review queue.

中文
====

用途
----
本包包含 21 个确定性路由任务。所有机器可读的 Skill 和部门字段都使用 main
中的规范英文 ID；中文仅保留为双语展示元数据和文档。

规范映射
--------
skill_name_map.json 是唯一的集中展示映射，记录 Skill ID、权威英文标题、
中文显示名、部门 ID、英文部门名、中文部门显示名及 main 中的来源。

实验隔离
--------
A、B、C 使用同一批任务提示，并且只能读取各自允许的 Skill 组织输入。
被测试 Codex 不得读取 Gold 或 evaluation 文件。Configuration C 可以把
main/skill_relations.json 作为路由输入，但评价器不会读取或依赖该图。

使用流程
--------
1. 审核 Gold Review 与 Skill 映射报告。
2. 运行 validate-package。
3. 使用规范英文 ID 运行 A、B、C 并保存预测。
4. 分别运行 evaluate。
5. 多次运行后执行 aggregate。
6. 查看指标、失败分析和人工复核队列。
