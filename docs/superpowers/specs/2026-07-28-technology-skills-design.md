# Technology Skills Design

## Goal

Create nine independent, composable Codex skills for the exact technology research, development, and system-operations workflow supplied by the project team. Eight skills cover the sequence from technology requirement through operations and maintenance; one provides an auditable technology database for architecture, systems, projects/code, APIs, tests, incidents/maintenance, and versions.

## Architecture

Use one skill package for each item in the supplied workflow so Codex loads only the instructions and resources needed for the current task. Preserve the supplied list, order, and scope without splitting, merging, adding, or removing skills.

The primary flow is:

`technology-requirement` → `technology-feasibility-assessment` → `technology-solution-design` → `technology-task-breakdown` → `technology-development-implementation` → `technology-test-acceptance` → `technology-system-release` → `technology-operations-maintenance`

`technology-database` supports every stage and records each confirmed mutation in an append-only audit log.

## Packages

1. `technology-requirement`
   - Capture business outcome, users, scope, functional and non-functional requirements, dependencies, constraints, acceptance criteria, risks, and evidence.
   - Use `assets/technology_requirement_template.md` to produce a versioned requirement baseline.
2. `technology-feasibility-assessment`
   - Assess technical, operational, security/privacy, schedule, staffing, cost, dependency, and migration feasibility.
   - Use `assets/feasibility_assessment_template.md`; provide evidence-backed options and reserve the go/no-go decision for authorized humans.
3. `technology-solution-design`
   - Define architecture, components, data flow, interfaces, security controls, capacity, observability, deployment, rollback, and decision records.
   - Use `assets/technical_design_template.md`; do not claim review or approval without evidence.
4. `technology-task-breakdown`
   - Convert an approved design into small, owned, testable tasks with dependencies and acceptance criteria.
   - Use `scripts/validate_task_plan.py` to reject duplicate IDs, missing dependencies, cycles, missing owners, and incomplete acceptance criteria.
5. `technology-development-implementation`
   - Guide code/configuration changes through branch scope, test-first implementation, review, evidence, and handoff.
   - Use `assets/implementation_record_template.md`; never claim build, review, merge, or deployment success without fresh evidence.
6. `technology-test-acceptance`
   - Use `scripts/evaluate_test_acceptance.py` to aggregate required test suites, executed/passed counts, blocking defects, evidence references, and acceptance status.
   - Keep product/technical acceptance under named human authority.
7. `technology-system-release`
   - Use `scripts/validate_release_manifest.py` and `assets/release_runbook_template.md` to validate artifact identity, approvals, change window, health checks, rollback, backup, ownership, and communications.
   - Never execute a production deployment or rollback without explicit scope and authorization.
8. `technology-operations-maintenance`
   - Use `assets/incident_maintenance_template.md` for monitoring, incident response, diagnosis, mitigation, recovery, root-cause analysis, maintenance, and follow-up.
   - Treat severity, customer communication, emergency change, closure, and destructive remediation as human decisions.
9. `technology-database`
   - Use `scripts/technology_db.py` and `references/technology_schema.md` for controlled SQLite operations.
   - Store architectures, systems, projects, code repository references, API documents, test records, incidents, maintenance records, system versions, and append-only audit events.

## Common Skill Contract

Each package contains a concise `SKILL.md` with only `name` and a trigger-oriented `description` in YAML frontmatter. The body contains Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes, plus an English workflow and a `**中文摘要：**` line. Each package also contains `agents/openai.yaml` whose default prompt explicitly invokes the corresponding `$skill-name`.

## Data Flow and Statuses

- Stable identifiers link `requirement_id`, `feasibility_id`, `design_id`, `task_plan_id`, `implementation_id`, `test_run_id`, `release_id`, `incident_id`, `maintenance_id`, `system_id`, and `version_id`.
- Every downstream step preserves upstream IDs, versions, source references, decision status, and responsible owner.
- Standard statuses distinguish `draft`, `pending_review`, `approved`, `rejected`, `in_progress`, `blocked`, `implemented`, `passed`, `failed`, `ready`, `released`, `rolled_back`, `resolved`, and `closed`.
- Corrections create a new version or linked superseding record; audit entries remain append-only.
- Environment is explicit: local, development, test, staging, or production. Evidence from one environment is not silently treated as evidence for another.

## Deterministic Tool Contracts

### Task Plan Validation

`validate_task_plan(plan: dict) -> dict` requires a stable plan ID, approved design reference, non-empty tasks, unique task IDs, owner, deliverable, acceptance criteria, estimate, and dependencies. It rejects unknown dependencies and dependency cycles, returns a deterministic topological execution order, and keeps scheduling/assignment decisions under human review.

### Test Acceptance Evaluation

`evaluate_test_acceptance(data: dict) -> dict` validates required suites and their evidence, recomputes executed/passed/failed/skipped totals, checks minimum pass rate and coverage thresholds when supplied, and blocks acceptance for missing suites, failed required tests, open critical/high defects, or missing evidence. It returns `acceptance_status: human_review_required` when automated gates pass.

### Release Manifest Validation

`validate_release_manifest(manifest: dict) -> dict` validates release/system/version/environment IDs, immutable artifact digest, approved change reference, release and rollback owners, deployment/rollback steps, backup and recovery references, health checks, monitoring/alerting, maintenance window, and communication plan. Production readiness requires explicit human approval evidence but the tool never deploys.

### Technology Database

`technology_db.py` exposes `connect_database`, `initialize_database`, `upsert_record`, and `query_record`. Supported entity types are architecture, system, project, code repository, API document, test record, incident, maintenance record, and system version. Mutations use explicit field allowlists, parameterized SQL, transactions, foreign keys, stable IDs, and audit records containing actor, business purpose, evidence reference, before/after JSON, action, and UTC timestamp.

## Database Boundaries

The SQLite database is a local demonstration, not a source-code host, CI/CD platform, observability backend, secrets manager, ticket system, configuration management database, or production system of record. It stores metadata and restricted references, not source code bodies, credentials, tokens, private keys, customer data, full logs, database dumps, or binary artifacts.

Query responses return only requested allowlisted fields. Database writes require explicit human confirmation, an authorized actor, a business purpose, and evidence reference.

## Safety and Control Boundaries

- Require authorized human decisions for requirement baseline, feasibility go/no-go, architecture approval, scope/assignment, code review/merge, test acceptance, production release/rollback, incident severity/closure, maintenance execution, and database mutations.
- Do not invent system state, performance results, security findings, code review, test output, approvals, deployments, recovery, incident resolution, or version status.
- Do not expose or store secrets, credentials, private keys, personal/customer data, raw production logs, or proprietary source code in general-purpose outputs or tables.
- Do not merge code, modify protected branches, deploy to production, change live infrastructure, rotate credentials, delete data, disable controls, or announce external status without explicit authority.
- Surface unknowns, unsupported assumptions, dependency risks, security/privacy gaps, failed tests, blocking defects, missing rollback evidence, monitoring gaps, and unresolved incidents.
- Keep legal, regulatory, privacy, safety, licensing, security acceptance, and business-risk decisions with qualified authorized humans.

## Error Handling

Scripts fail closed on missing identifiers, duplicate task IDs, broken dependencies, cycles, inconsistent test counts, invalid thresholds, missing evidence, blocking defects, mutable or malformed artifact identifiers, absent approval/rollback controls, duplicate stable identifiers, broken foreign keys, unsupported fields, and invalid status transitions. Database mutations are transactional so failed validation leaves no partial record or audit event.

## Testing Strategy

- Add `tests/test_technology_skills.py` first and confirm each of the nine package-specific tests fails before implementation.
- Add behavior tests before each deterministic script:
  - `tests/test_validate_task_plan.py` covers valid order, duplicate IDs, missing dependencies, cycles, missing owner/acceptance, and invalid estimates.
  - `tests/test_evaluate_test_acceptance.py` covers hand-checked totals, missing suites/evidence, failed tests, defects, coverage/pass thresholds, and human review status.
  - `tests/test_validate_release_manifest.py` covers a complete staging/production manifest, missing approvals, malformed digest, missing rollback/health/monitoring controls, and non-production behavior.
  - `tests/test_technology_db.py` covers schema, audited mutations for every entity, uniqueness, foreign keys, validation, minimum-field queries, confirmation, and rollback.
- Run the full unittest suite after every package is green.
- Run the official Codex validator for all nine packages and scan for placeholders and broken resource links.
- Exercise the workflow with fictional local/staging data only; do not modify external systems.

## Non-Goals

- Live Git hosting, CI/CD, cloud, cluster, monitoring, ticketing, secrets, asset-management, or production integrations
- Autonomous code merging, infrastructure changes, production release/rollback, credential rotation, destructive remediation, or incident closure
- A universal software-development methodology or jurisdiction-specific compliance/security certification
- Storage of source code bodies, secrets, production data, raw logs, artifacts, or full design/contract documents

## Success Criteria

- All nine packages are valid, discoverable Codex skills matching the supplied list and order.
- Workflow relationships, evidence requirements, environments, and human decision boundaries are explicit.
- Deterministic scripts produce transparent, reproducible results and reject unsafe or inconsistent inputs.
- The technology database represents every requested record category with audited, transactional mutations.
- Existing HR, finance, and procurement tests pass together with all technology tests.
