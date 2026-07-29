# Change Report

## Scope

This local review package converts SkillNet Gold Tasks V4 to canonical English
machine identifiers with complete English content and retained Chinese display
content. It is based on `main@cdb4ecdf838fdd4e0bbb01e4c766b32eb430eb47`.

No remote branch, pull request, or merge was created or changed.

## Files changed

- `01_Codex_Test_Prompts_21_V4.txt`
  - Added a complete independently runnable English instruction set and all 21
    English task prompts.
  - Retained a complete Chinese instruction summary and all 21 Chinese prompts.
  - Requires canonical Skill IDs and canonical department IDs in predictions.
- `02_Gold_Standard_21_V4.json`
  - Replaced Chinese machine identifiers with exact canonical IDs from main.
  - Added paired English/Chinese titles, prompts, rationales, and scoring notes.
  - Added `forbid_all_skills` for no-tool tasks.
  - Removed the noncanonical all-Skills string sentinel.
  - Set `aliases` to an empty object so exact canonical IDs are required.
- `03_Gold_Tasks_Review_21_V4.md`
  - Rebuilt as a complete bilingual review generated from the converted Gold.
- `04_Task_Coverage_Matrix_V4.csv`
  - Added English column names and English titles.
  - Retained Chinese title and relation-display columns.
  - Uses canonical department IDs and authoritative relation-type names.
- `05_Evaluation_Design_CN.md`
  - Replaced by `05_Evaluation_Design_BILINGUAL.md`.
  - Added a complete English design and a complete Chinese design.
- `README_V4.txt`
  - Rewritten as a complete bilingual package guide.
- `evaluation/README_EVALUATION.txt`
  - Rewritten as a complete bilingual evaluator guide.
- `evaluation/evaluate_skillnet.py`
  - Uses canonical Skill and department IDs through the converted Gold catalog.
  - Validates canonical ID syntax and department membership.
  - Detects unknown IDs in both `skill_sequence` and `blocked_by`.
  - Implements `forbid_all_skills` without a noncanonical sentinel.
  - Requires blocked flows to stop without executing further Skills.
  - Tightens no-tool correctness to require empty department, Skill, blocker, and
    route fields.
  - Adds Department Precision and Recall, No-Tool Accuracy, and Blocked-Flow
    Accuracy to summaries while preserving all existing metrics and failure tags.
- `evaluation/prediction_schema.json`
  - Constrains Skill and department values to canonical enums.
  - Adds status-specific completed, blocked, and no-tool conditions.
  - Disallows unrecognized top-level fields.
- All 21 files under `prompts/`
  - Added complete English and Chinese task text.
  - Added canonical-ID output requirements.
- `results/package_validation_report.json`
  - Regenerated from the bilingual package.

## Files added

- `skill_name_map.json`
  - Single central display mapping for all 46 Skills and five departments.
- `SKILL_NAME_MAPPING_REPORT.md`
  - Human-readable complete mapping inventory and source audit.
- `evaluation/fixtures/gold_perfect_predictions.jsonl`
  - A 21-task deterministic validation fixture.
- `evaluation/fixtures/valid_status_samples.jsonl`
  - Schema-valid completed, blocked, and no-tool examples.
- `evaluation/tests/test_evaluator.py`
  - Regression tests for canonical mapping, semantic preservation, schema,
    metrics, partial orders, and failure detection.
- `CHANGE_REPORT.md`
- `VALIDATION_REPORT.md`
- `GIT_INTEGRATION_PLAN.md`

## Schema changes

- Machine fields use canonical IDs:
  - `selected_departments`: exact department IDs such as `finance-agent`.
  - `skill_sequence` and `blocked_by`: exact Skill directory IDs.
- `02_Gold_Standard_21_V4.json` replaces Chinese-only text fields with paired
  `_en` and `_zh` fields.
- `skill_catalog` maps canonical Skill IDs to canonical department IDs.
- `department_catalog` contains canonical department IDs.
- `forbid_all_skills` replaces the legacy noncanonical all-Skills sentinel.
- Chinese names are retained only in display or bilingual text fields.

## Evaluator behavior preserved

The task meanings, task IDs, Gold-required/optional/forbidden semantics, initial
states, partial orders, route decisions, blocker decisions, deterministic scoring,
approved metrics, and existing failure tags are preserved.

The evaluator remains a deterministic structured-data evaluator. It does not use
an LLM or a global graph input.

## Intentionally unchanged

- All 21 task IDs.
- The meaning, current state, target, and restrictions of every task.
- `evaluation/predictions_template.jsonl` remains a deliberately incomplete
  fill-in template; it becomes schema-valid only after placeholders are replaced.
- `evaluation/run_all_example.sh` retains the same command workflow because the
  Gold path and evaluator CLI remain compatible.
- Prediction output directories and `.gitkeep` files remain unchanged.
- Configuration C may still use the repository's canonical relation file as a
  routing input, but the evaluator does not depend on it.
