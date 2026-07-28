# SkillNet A/B/C Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a reproducible 21-task, three-configuration benchmark that measures Codex's autonomous selection and ordering of the 46 atomic enterprise Skills.

**Architecture:** Keep Gold answers and the deterministic evaluator outside every candidate Codex workspace. Each run receives the same 46 `.agents/skills` packages and one task prompt; Configuration A receives no organization metadata, B receives department grouping metadata, and C receives the advisory Skill relation graph. Codex chooses the route itself and returns a schema-constrained JSON prediction that is scored offline against task-level Gold rules.

**Tech Stack:** Python 3 standard library, `unittest`, Codex CLI `exec`, JSON/JSONL/CSV, Git.

## Global Constraints

- Use the exact English YAML/folder slug for every machine-facing Skill identifier.
- Keep all 46 existing project Skills unchanged.
- Keep Chinese business prompts so all configurations receive identical natural-language tasks.
- Do not expose Gold Standard, evaluator code, results, or another configuration's metadata to candidate Codex runs.
- Do not use a hard router; B and C provide advisory organization data only.
- Run every task in a new ephemeral Codex session with the same model, reasoning effort, sandbox, output schema, and prompt wrapper.
- Do not execute real finance, procurement, technology, business, or HR actions.

---

### Task 1: Import and Canonicalize Gold Tasks V4

**Files:**
- Import: `SkillNet_Gold_Tasks_V4/**`
- Create: `tests/test_skillnet_evaluation_package.py`
- Modify: `SkillNet_Gold_Tasks_V4/02_Gold_Standard_21_V4.json`
- Modify: `SkillNet_Gold_Tasks_V4/01_Codex_Test_Prompts_21_V4.txt`
- Modify: `SkillNet_Gold_Tasks_V4/prompts/*.txt`

**Interfaces:**
- Consumes: the 46 directory/YAML names under `.agents/skills`.
- Produces: a Gold package whose catalog, task rules, sequences, blockers, aliases, and output instructions use those exact slugs.

- [ ] Import commit `329e95f` without merging the obsolete HR-only branch history.
- [ ] Add a test that compares Gold `skill_catalog` keys exactly with the 46 `.agents/skills` directories and verifies every task-level Skill reference is canonical.
- [ ] Run the test and confirm it fails on the Chinese identifiers.
- [ ] Convert all machine-facing Skill identifiers to English slugs while preserving Chinese task prose and human-readable titles.
- [ ] Update output instructions and per-task prompt files to require exact English slugs.
- [ ] Run the test and confirm it passes.

### Task 2: Define and Isolate Configurations A, B, and C

**Files:**
- Create: `SkillNet_Gold_Tasks_V4/configurations/configurations.json`
- Create: `SkillNet_Gold_Tasks_V4/configurations/A/AGENTS.md`
- Create: `SkillNet_Gold_Tasks_V4/configurations/B/AGENTS.md`
- Create: `SkillNet_Gold_Tasks_V4/configurations/B/department_groups.json`
- Create: `SkillNet_Gold_Tasks_V4/configurations/C/AGENTS.md`
- Create: `SkillNet_Gold_Tasks_V4/configurations/C/skill_relations.json`
- Create: `SkillNet_Gold_Tasks_V4/evaluation/run_experiments.py`
- Test: `tests/test_skillnet_evaluation_package.py`

**Interfaces:**
- Consumes: repository `.agents/skills`, the approved A/B/C definitions, and individual prompt files.
- Produces: `prepare_candidate_workspace(...)` and `build_candidate_prompt(...)`, which create a temporary workspace containing only the allowed treatment data.

- [ ] Add tests asserting all configurations expose exactly 46 Skills, never expose Gold/evaluation files, A has no grouping or graph, B has only department grouping, and C has only the relation graph.
- [ ] Run the tests and confirm they fail because the manifests and workspace builder do not exist.
- [ ] Implement the manifests and minimal workspace builder.
- [ ] Run the tests and confirm they pass.

### Task 3: Harden Deterministic Evaluation

**Files:**
- Modify: `SkillNet_Gold_Tasks_V4/evaluation/evaluate_skillnet.py`
- Test: `tests/test_skillnet_evaluation_package.py`

**Interfaces:**
- Consumes: schema-constrained prediction objects and task-level Gold records.
- Produces: strict functional/clean success results that reject unknown or extra blockers and unexpected route-choice entries.

- [ ] Add regression tests showing that extra/unknown `blocked_by` entries and unexpected route-choice fields are rejected.
- [ ] Run the tests and confirm they fail against the imported evaluator.
- [ ] Implement strict blocker and route-choice comparison plus failure tags.
- [ ] Run the tests and confirm they pass.
- [ ] Run `validate-package` and a canonical-sequence smoke evaluation.

### Task 4: Implement the Codex Runner and Smoke Test

**Files:**
- Modify: `SkillNet_Gold_Tasks_V4/evaluation/run_experiments.py`
- Modify: `SkillNet_Gold_Tasks_V4/README_V4.txt`
- Modify: `SkillNet_Gold_Tasks_V4/05_Evaluation_Design_CN.md`
- Modify: `SkillNet_Gold_Tasks_V4/evaluation/README_EVALUATION.txt`
- Test: `tests/test_skillnet_evaluation_package.py`

**Interfaces:**
- Consumes: configuration name, task IDs, Codex executable, model, reasoning effort, run ID, and concurrency limit.
- Produces: one normalized JSON prediction and one diagnostic log per task plus a run manifest recording the controlled settings.

- [ ] Add tests for command construction, prediction normalization, retry/error records, and run-manifest metadata.
- [ ] Run the tests and confirm they fail before runner implementation.
- [ ] Implement independent ephemeral `codex exec` calls with read-only sandboxing and JSON Schema output.
- [ ] Document exact A/B/C inputs and reproduction commands.
- [ ] Run tests and then one task in A, B, and C as an authenticated Codex smoke test.

### Task 5: Run and Aggregate the Full Experiment

**Files:**
- Generate: `SkillNet_Gold_Tasks_V4/predictions/{A,B,C}/run_01/*.json`
- Generate: `SkillNet_Gold_Tasks_V4/predictions/{A,B,C}/run_01/run_manifest.json`
- Generate: `SkillNet_Gold_Tasks_V4/results/{A,B,C}_run_01/**`
- Generate: `SkillNet_Gold_Tasks_V4/results/summary/**`

**Interfaces:**
- Consumes: all 21 prompts for each of A, B, and C.
- Produces: 63 prediction records, per-task metrics, per-configuration summaries, paired task comparisons, and failure analysis.

- [ ] Run all 21 independent tasks for A with the fixed Codex settings.
- [ ] Run all 21 independent tasks for B with the same settings.
- [ ] Run all 21 independent tasks for C with the same settings.
- [ ] Evaluate each run and aggregate A/B/C.
- [ ] Verify exactly 21 parseable predictions per configuration with no missing task IDs.
- [ ] Run the full repository test suite, Gold package validation, script syntax checks, and `git diff --check`.
- [ ] Summarize functional success, clean success, Skill F1, order accuracy, constraint violations, and notable task-level differences.
