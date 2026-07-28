---
name: technology-system-release
description: Use when a tested system version needs artifact, approval, deployment, health-check, monitoring, backup, rollback, change-window, or communication readiness review.
---

# Technology System Release

## Overview

Prepare a controlled, observable, reversible system release without confusing readiness validation with deployment execution.

**中文摘要：** 核验系统版本、不可变制品、测试验收、审批、变更窗口、上线步骤、健康检查、监控、备份与回滚方案；不得自动执行生产发布。

## Required Inputs

- Release/system/version IDs, target environment, immutable artifact digest, source commit/build, and test acceptance
- Approved change, release/rollback owners, maintenance window, dependencies, freeze/exception policy, and access authority
- Deployment steps, configuration/migration plan, backup/recovery evidence, health checks, monitoring/alerts, and rollback criteria
- Stakeholders, communication/status route, incident escalation, and production approval evidence when applicable

## Workflow

1. Read `assets/release_runbook_template.md`; assign `release_id` and preserve artifact/version traceability.
2. Verify the immutable artifact, environment, configuration, dependencies, test acceptance, change record, access, and approvals.
3. Run `scripts/validate_release_manifest.py`; resolve every blocking readiness finding.
4. Rehearse deployment, migration, health checks, monitoring, rollback triggers/steps, backup restore, and ownership in a safe environment.
5. Define pre-change snapshot, go/no-go checkpoint, change sequence, verification window, stop conditions, and communication timing.
6. At execution time, re-check current state, authorization, window, evidence, and competing incidents/changes.
7. Record each action and observation; stop or roll back according to approved triggers.
8. Route production release, rollback, exception, and completion decisions to authorized humans.

## Output Contract

Return release/system/version/environment IDs, digest, change/test evidence, readiness checks/findings, runbook, owners, window, health/monitoring, rollback/backup, communications, approvals, `release_status`, and `external_action`.

## SkillNet Relationships

- Follows `technology-test-acceptance` and precedes `technology-operations-maintenance`.
- Supplies released-version and runbook evidence to operations.
- Persists confirmed release/version metadata through `technology-database`.

## Guardrails

- Do not invent artifacts, tests, approvals, backups, deployment, health, monitoring, rollback, or completion evidence.
- Do not deploy, change live configuration, migrate/delete data, disable controls, or announce status outside explicit authority.
- Human approval is required for go/no-go, production release, rollback, exception, migration, and completion.

## Example

Validate onboarding version 1.4 for staging using its SHA-256 digest, accepted tests, owners, backup, deployment, health checks, monitoring, rollback, and communications.

## Common Mistakes

- Deploying a mutable tag instead of a verified artifact digest
- Treating staging evidence as production approval
- Missing tested rollback triggers, ownership, monitoring, or backup recovery
- Claiming release completion from manifest readiness alone
