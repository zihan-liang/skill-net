---
name: technology-development-implementation
description: Use when an approved technical task requires source-code, configuration, infrastructure-as-code, integration, migration, or system implementation with test and review evidence.
---

# Technology Development and Implementation

## Overview

Implement one approved technical scope through evidence-first, reversible changes while protecting existing work and keeping merge/deployment authority with humans.

**中文摘要：** 按已批准任务实施代码、配置或系统变更，遵循测试先行、最小范围、可回滚和证据交付；不得自动声称评审、合并或部署完成。

## Required Inputs

- Approved task/design/requirement IDs and versions, owner, scope, deliverable, and acceptance criteria
- Repository/system/environment boundaries, existing conventions, dependencies, and build/test commands
- Data/security/privacy constraints, migration/compatibility needs, review policy, and change authority
- Rollback approach, evidence location, handoff recipient, and prohibited operations

## Workflow

1. Read `assets/implementation_record_template.md`; assign `implementation_id` and preserve upstream traceability.
2. Inspect current state, instructions, working-tree changes, dependencies, and baseline tests before editing.
3. Confirm the smallest change that satisfies the approved acceptance criteria; surface scope conflicts.
4. Write a failing test or reproducible validation before implementation, then make the minimum change to pass.
5. Preserve unrelated work; validate inputs, failures, permissions, secrets handling, compatibility, and rollback behavior.
6. Run targeted and full verification; record exact commands, environment, timestamps, outputs, and residual risks.
7. Review the diff against scope, design, security, operations, documentation, and migration requirements.
8. Prepare a review-ready handoff; do not claim review, merge, release, or deployment without fresh evidence.

## Output Contract

Return `implementation_id`, upstream IDs, repository/environment, changed artifacts, decisions, test-first evidence, verification results, review findings, migration/rollback notes, residual risks, handoff, and evidence-based `implementation_status`.

## SkillNet Relationships

- Follows `technology-task-breakdown` and precedes `technology-test-acceptance`.
- Supplies version, change, test, and rollback evidence to release and operations Skills.
- Stores confirmed metadata through `technology-database`, never source bodies.

## Guardrails

- Do not invent code state, test results, review, merge, deployment, or rollback evidence.
- Do not expose secrets, overwrite unrelated changes, alter protected branches, or mutate live systems outside explicit scope.
- Human approval is required for scope expansion, destructive migration, merge, production change, and exception acceptance.

## Example

Implement one onboarding API task on a feature branch, demonstrate the failing/passing contract test, run the full suite, document migration and rollback, and prepare review evidence.

## Common Mistakes

- Editing before checking current state and user changes
- Testing only the happy path or only after implementation
- Expanding scope through opportunistic refactoring
- Saying “implemented” or “reviewed” without fresh command and diff evidence
