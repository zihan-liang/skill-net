# Technology Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the nine technology Codex skills in the exact order and scope supplied by the project team.

**Architecture:** Keep each workflow item in an independent `skills/technology-*` package with concise instructions and generated UI metadata. Use Markdown assets for human-reviewed records and Python standard-library scripts for task dependency validation, test acceptance, release-manifest validation, and transactional SQLite storage.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, SQLite, Codex `skill-creator` initialization and validation scripts.

## Global Constraints

- Preserve exactly these nine skills and this order: technology requirement, feasibility assessment, solution design, task breakdown, development/implementation, test acceptance, system release, operations/maintenance, technology database.
- Keep every `SKILL.md` below 500 words with only `name` and trigger-oriented `description` frontmatter.
- Include Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes.
- Include an English workflow and a `**中文摘要：**` line in every skill.
- Require authorized human decisions for baselines, go/no-go, architecture, assignment, merge, acceptance, production release/rollback, incident closure, maintenance, and database mutation.
- Never claim tests, reviews, deployment, recovery, or system state without fresh evidence; never modify a live external system in demonstrations.
- Store only metadata/references in the technology database, never source bodies, secrets, customer data, raw logs, or binary artifacts.
- Record database mutations with actor, business purpose, evidence reference, before/after values, confirmation, and UTC timestamp.
- Create every package through `skill-creator/scripts/init_skill.py` and validate it with `quick_validate.py`.

---

### Task 1: Technology Requirement Skill

**Files:**
- Create: `tests/test_technology_skills.py`
- Create: `skills/technology-requirement/SKILL.md`
- Create: `skills/technology-requirement/agents/openai.yaml`
- Create: `skills/technology-requirement/assets/technology_requirement_template.md`

**Interfaces:**
- Consumes: requester, business outcome, users, scope, functions, quality attributes, dependencies, constraints, evidence, and acceptance criteria.
- Produces: `requirement_id`, version, prioritized requirements, assumptions, risks, missing information, sources, and `status: draft`.

- [ ] Write a failing structural contract whose `test_requirement` calls `validate_skill("technology-requirement")`; validate metadata, headings, Chinese summary, human boundary, resources, word count, placeholder absence, and `$technology-requirement` UI prompt.
- [ ] Run `python3 -m unittest tests.test_technology_skills.TechnologySkillContractTests.test_requirement` and confirm failure because the package is absent.
- [ ] Initialize with `assets`, replace generated content, and create a versioned requirement template.
- [ ] Run the targeted test, official validator, and existing green tests; commit with `feat: add technology requirement skill`.

### Task 2: Feasibility Assessment Skill

**Files:**
- Create: `skills/technology-feasibility-assessment/SKILL.md`
- Create: `skills/technology-feasibility-assessment/agents/openai.yaml`
- Create: `skills/technology-feasibility-assessment/assets/feasibility_assessment_template.md`

**Interfaces:**
- Consumes: approved requirement, current architecture/system evidence, options, constraints, staff, schedule, cost, security/privacy, dependencies, and migration needs.
- Produces: `feasibility_id`, option matrix, assumptions, evidence gaps, risks/mitigations, prototype needs, recommendation, and `decision_status: human_review_required`.

- [ ] Run the already-written `test_feasibility_assessment` and confirm its absent-package failure.
- [ ] Initialize with `assets`, implement the evidence-backed assessment workflow, and create the assessment template.
- [ ] Run targeted/full tests and official validation; commit with `feat: add technology feasibility assessment skill`.

### Task 3: Solution Design Skill

**Files:**
- Create: `skills/technology-solution-design/SKILL.md`
- Create: `skills/technology-solution-design/agents/openai.yaml`
- Create: `skills/technology-solution-design/assets/technical_design_template.md`

**Interfaces:**
- Consumes: approved requirement and feasibility decision, constraints, current architecture, data classifications, integrations, quality attributes, and review policy.
- Produces: `design_id`, version, components, data flow, interfaces, decisions/trade-offs, security, capacity, observability, deployment/rollback, risks, and `status: draft`.

- [ ] Run `test_solution_design` and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement the design workflow, and create the technical design template.
- [ ] Run targeted/full tests and validation; commit with `feat: add technology solution design skill`.

### Task 4: Task Breakdown Skill and Validator

**Files:**
- Create: `tests/test_validate_task_plan.py`
- Create: `skills/technology-task-breakdown/SKILL.md`
- Create: `skills/technology-task-breakdown/agents/openai.yaml`
- Create: `skills/technology-task-breakdown/scripts/validate_task_plan.py`

**Interfaces:**
- Produces: `validate_task_plan(plan: dict) -> dict`.
- Returns: plan/design IDs, task count, deterministic topological order, dependency edges, total estimate, blocking findings, and `assignment_status: human_review_required`.

- [ ] Write literal behavior tests for a valid dependency order, duplicate IDs, unknown dependencies, cycles, missing owner/deliverable/acceptance, and non-positive estimates; confirm import failure.
- [ ] Run structural `test_task_breakdown` and confirm the absent-package failure.
- [ ] Initialize with `scripts`; implement validation and a JSON CLI using no external dependency.
- [ ] Run behavior/structural/full tests and official validation; commit with `feat: add technology task breakdown skill`.

### Task 5: Development or Implementation Skill

**Files:**
- Create: `skills/technology-development-implementation/SKILL.md`
- Create: `skills/technology-development-implementation/agents/openai.yaml`
- Create: `skills/technology-development-implementation/assets/implementation_record_template.md`

**Interfaces:**
- Consumes: approved design/task, repository/environment scope, acceptance criteria, test command, review policy, and change authority.
- Produces: `implementation_id`, changed artifacts, test-first evidence, review findings, residual risks, handoff, and `implementation_status` based only on evidence.

- [ ] Run `test_development_implementation` and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement the scoped test-first/change-review workflow, and create the evidence record.
- [ ] Run targeted/full tests and validation; commit with `feat: add technology development implementation skill`.

### Task 6: Test Acceptance Skill and Evaluator

**Files:**
- Create: `tests/test_evaluate_test_acceptance.py`
- Create: `skills/technology-test-acceptance/SKILL.md`
- Create: `skills/technology-test-acceptance/agents/openai.yaml`
- Create: `skills/technology-test-acceptance/scripts/evaluate_test_acceptance.py`

**Interfaces:**
- Produces: `evaluate_test_acceptance(data: dict) -> dict`.
- Returns: recomputed totals/pass rate, required-suite coverage, coverage threshold result, blocking defects/findings, evidence references, automated gate result, and human acceptance status.

- [ ] Write hand-checked tests for passing suites, missing required suite/evidence, inconsistent counts, failed tests, critical/high defects, and missed pass/coverage thresholds; confirm import failure.
- [ ] Run structural `test_test_acceptance` and confirm the absent-package failure.
- [ ] Initialize with `scripts`; implement Decimal-safe aggregation and a JSON CLI.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add technology test acceptance skill`.

### Task 7: System Release Skill, Runbook, and Manifest Validator

**Files:**
- Create: `tests/test_validate_release_manifest.py`
- Create: `skills/technology-system-release/SKILL.md`
- Create: `skills/technology-system-release/agents/openai.yaml`
- Create: `skills/technology-system-release/assets/release_runbook_template.md`
- Create: `skills/technology-system-release/scripts/validate_release_manifest.py`

**Interfaces:**
- Produces: `validate_release_manifest(manifest: dict) -> dict`.
- Returns: release/system/version/environment IDs, artifact digest, readiness checks/findings, release/rollback owners, approval evidence, and `release_status: ready_for_human_release` or `blocked`.

- [ ] Write tests for a complete staging/production manifest, production approval, malformed digest, missing rollback steps, missing health/monitoring controls, and non-production approval behavior; confirm import failure.
- [ ] Run structural `test_system_release` and confirm the absent-package failure.
- [ ] Initialize with `scripts,assets`; implement fail-closed validation, JSON CLI, and the runbook template.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add technology system release skill`.

### Task 8: Operations and Maintenance Skill

**Files:**
- Create: `skills/technology-operations-maintenance/SKILL.md`
- Create: `skills/technology-operations-maintenance/agents/openai.yaml`
- Create: `skills/technology-operations-maintenance/assets/incident_maintenance_template.md`

**Interfaces:**
- Consumes: system/version/environment, monitoring evidence, alert/incident, runbook, service objectives, change authority, maintenance scope, and communication route.
- Produces: incident/maintenance IDs, timeline, impact, evidence, actions, current state, recovery validation, RCA/follow-ups, owners, and human decision statuses.

- [ ] Run `test_operations_maintenance` and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement monitor/triage/mitigate/recover/RCA/maintenance workflows, and create the incident/maintenance record.
- [ ] Run targeted/full tests and validation; commit with `feat: add technology operations maintenance skill`.

### Task 9: Technology Database Skill and SQLite Tool

**Files:**
- Create: `tests/test_technology_db.py`
- Create: `skills/technology-database/SKILL.md`
- Create: `skills/technology-database/agents/openai.yaml`
- Create: `skills/technology-database/scripts/technology_db.py`
- Create: `skills/technology-database/references/technology_schema.md`

**Interfaces:**
- Produces: `connect_database`, `initialize_database`, `upsert_record`, and `query_record`.
- Supported entities: architecture, system, project, code repository, API document, test record, incident, maintenance record, and system version; every mutation returns the stored record and `audit_event_id`.

- [ ] Write tests for all tables, one mutation per entity, human confirmation, unique repository/version identifiers, foreign keys, environment/status validation, secret/source-body field rejection, minimum queries, before/after audits, and rollback; confirm import failure.
- [ ] Run structural `test_database` and confirm the absent-package failure.
- [ ] Initialize with `scripts,references`; implement allowlisted parameterized SQLite operations, append-only audit triggers, and schema documentation.
- [ ] Run database/structural/full tests and validation; commit with `feat: add technology database skill`.

### Task 10: Collection Verification and Demonstration

**Files:**
- Modify: `.gitignore` only if disposable database or cache artifacts are not already excluded.

**Interfaces:**
- Consumes: all nine packages and tests.
- Produces: a validated technology skill collection and fictional local/staging demonstration output.

- [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'` and require zero failures.
- [ ] Run `quick_validate.py` on every `skills/technology-*` directory.
- [ ] Run `git diff --check`, compile scripts, execute each script's `--help`, scan for incomplete placeholders, validate resource references, and check every skill is below 500 words.
- [ ] With fictional data, validate a task plan, evaluate a test run, validate a staging release manifest, initialize a disposable database, write all record categories, query minimum fields, and inspect audit events; perform no external mutation.
- [ ] Review the diff for exact nine-skill scope and safety, then commit any final technology-only corrections.
