---
name: technology-operations-maintenance
description: Use when a running system needs monitoring review, incident triage, diagnosis, mitigation, recovery validation, root-cause analysis, or planned maintenance; not for release readiness.
---

# Technology Operations and Maintenance

## Overview

Coordinate evidence-based operations, incident response, recovery, and planned maintenance while keeping live-system actions and customer decisions under explicit authority.

**中文摘要：** 负责系统监控、故障响应、诊断、缓解、恢复验证、根因分析和计划维护；严重级别、生产操作、对外沟通与关闭必须由授权人员决定。

## Required Inputs

- System/version/environment, owner/on-call, service objectives, runbooks, dependencies, and current change history
- Alert/incident/maintenance ID, timestamps, symptoms, user/business impact, logs/metrics/traces, and evidence references
- Access/change authority, backup/recovery state, security/privacy implications, escalation, and communication route
- Proposed diagnosis, mitigation, maintenance steps, validation, rollback, owner, and schedule

## Workflow

1. Read `assets/incident_maintenance_template.md`; choose incident or planned-maintenance mode and assign a stable ID.
2. Verify system/version/environment, signal source, timeline, impact, current health, owners, and active changes.
3. For incidents, preserve evidence; triage severity, security/privacy risk, scope, dependencies, and escalation with humans.
4. Form testable hypotheses and run the safest read-only diagnostics before mutation.
5. Propose mitigation/recovery with expected outcome, risk, authorization, stop condition, rollback, and observer.
6. After authorized action, verify service, data integrity, security, dependencies, monitoring, and user outcome with fresh evidence.
7. For maintenance, validate window, backup, steps, health checks, rollback, conflicts, and communications before execution.
8. Document timeline, cause/contributing factors, lessons, corrective/preventive actions, owners, due dates, and recurrence checks.

## Output Contract

Return incident/maintenance/system/version IDs, environment, impact, timeline, evidence, hypotheses, diagnostics, authorized actions, validation, current state, rollback, communications, root cause/contributors, follow-ups, owners, and human decision/closure statuses.

## SkillNet Relationships

- Part of `technology-agent`.
- Follows `technology-system-release`.

## Approval Controls

- Do not invent telemetry, impact, severity, cause, action, recovery, customer communication, or closure evidence.
- Do not expose secrets/customer data or execute destructive/live actions beyond explicit scope and authorization.
- Human approval is required for severity, production mutation, emergency change, rollback, data recovery, external communication, risk acceptance, and closure.

## Exception Handling

- Escalate security/privacy indicators, unknown blast radius, failed recovery, unavailable owner, or data-integrity risk immediately through the authorized route.
- Preserve evidence before mutation; stored incident status alone never proves recovery or closure.

## Handoff

Pass unresolved defects or change needs with system/version/environment, timeline, evidence, root cause confidence, risk, and acceptance criteria back to `technology-requirement`; pass ongoing actions to the named operations owner.

## Example

Triage elevated onboarding errors after version 1.4, preserve evidence, test a dependency-timeout hypothesis, propose a reversible mitigation, validate recovery, and create follow-ups.

## Common Mistakes

- Changing production before preserving evidence and defining rollback
- Treating correlation or the last deployment as proven root cause
- Closing after one green check without observation and user-impact validation
- Recording secrets, personal data, or raw production logs in the incident summary
