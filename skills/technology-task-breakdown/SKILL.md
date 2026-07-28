---
name: technology-task-breakdown
description: Use when an approved technical design needs to become owned, estimable, dependency-aware, testable implementation tasks or a reviewable delivery plan.
---

# Technology Task Breakdown

## Overview

Convert an approved design into small, independently verifiable tasks with explicit deliverables, dependencies, owners, estimates, and acceptance criteria.

**中文摘要：** 将已批准的技术方案拆解为可执行、可估算、可验收的任务，明确负责人、交付物、依赖关系和完成标准，避免循环或隐藏依赖。

## Required Inputs

- Approved `design_id`/version and approval evidence
- Requirement traceability, components, interfaces, data/migration, security, testing, release, and operations work
- Team roles/capacity, estimation unit, sequencing constraints, milestones, and definition of done
- Review, documentation, code ownership, environment, and handoff requirements

## Workflow

1. Define `task_plan_id` and preserve design/requirement versions.
2. Identify deliverable slices across implementation, data, integration, security, tests, documentation, release, observability, migration, and operations.
3. Make each task small enough to have one owner, one observable deliverable, and concrete acceptance criteria.
4. Record estimates as planning inputs, not promises; state unknowns and discovery tasks.
5. Link only genuine prerequisite task IDs and identify external dependencies separately.
6. Run `scripts/validate_task_plan.py` to detect incomplete tasks, unknown dependencies, duplicates, and cycles.
7. Review critical path, parallel work, capacity, risks, handoffs, and milestone evidence.
8. Route scope, priority, assignment, estimate, and schedule decisions to authorized humans.

## Output Contract

Return task-plan/design IDs, tasks with owner/deliverable/criteria/estimate/dependencies, dependency edges, deterministic execution order, total estimate, external dependencies, risks, milestones, evidence, and `assignment_status: human_review_required`.

## SkillNet Relationships

- Follows `technology-solution-design` and precedes `technology-development-implementation`.
- Supplies acceptance criteria to `technology-test-acceptance` and release/operations work items.
- Persists approved plan metadata through `technology-database`.

## Guardrails

- Do not invent owners, capacity, estimates, dependencies, dates, or approval evidence.
- Do not hide testing, security, documentation, migration, release, or operations work inside vague tasks.
- Human approval is required for scope, priority, assignment, milestones, commitments, and plan changes.

## Example

Break an onboarding-service design into schema, API, UI, security, migration, tests, observability, runbook, and release tasks with a cycle-free order.

## Common Mistakes

- Tasks defined as activities rather than observable deliverables
- Missing acceptance criteria or review/test evidence
- Circular, implicit, or ownerless dependencies
- Treating summed estimates as a committed delivery date
