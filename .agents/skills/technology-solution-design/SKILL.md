---
name: technology-solution-design
description: Use when approved technical specifications need architecture, components, data flow, deployment, observability, resilience, migration, and rollback design; not for confirming requirements or technical thresholds.
---

# Technology Solution Design

## Overview

Design how the confirmed technical specification will be implemented. Preserve the fixed performance, interface, compatibility, security, and acceptance obligations rather than redefining them.

**中文摘要：** 完成架构、组件、数据流、部署、可观测性、韧性、迁移和回滚方案；不重新定义技术规格与验收阈值。

## Required Inputs

- Approved requirement, feasibility, and specification IDs/versions with decision evidence
- Current architecture, systems, environments, ownership, dependencies, and restricted artifact references
- Fixed interface/security/compatibility/acceptance obligations and approved standards
- Deployment, observability, recovery, migration, rollback, cost, and review policies

## Workflow

1. Read `assets/technical_design_template.md`; assign `design_id` and version.
2. Preserve specification traceability and list design assumptions, exclusions, unknowns, and fixed constraints.
3. Define system context, architecture, components, responsibilities, dependencies, data ownership/flow, and storage.
4. Map confirmed interfaces and controls to component boundaries without changing their approved obligations.
5. Design failure isolation, resilience, backup/recovery, and capacity mechanisms that meet the fixed targets.
6. Design logs, metrics, traces, alerts, service objectives, operational ownership, and runbooks.
7. Define environments, deployment, configuration, migration, compatibility transition, health checks, rollback, and failure recovery.
8. Record alternatives, architecture decisions, trade-offs, verification mapping, risks, and required reviewers.

## Output Contract

Return design/specification IDs and versions, architecture/components, data flows, interface/control mapping, resilience, observability, deployment/migration/rollback, decisions/trade-offs, verification mapping, risks, sources, reviewers, and `status: draft`.

## SkillNet Relationships

- Part of `technology-agent`.
- Follows `technology-specification-confirmation`.
- Precedes `technology-task-breakdown`.

## Approval Controls

- Use stable IDs, restricted document/source references, reviewers, actor/purpose, and append-only version/audit evidence; do not store secrets or source-code bodies.
- Do not invent architecture state, benchmarks, guarantees, compatibility, approval, or review evidence.
- Human approval is required for architecture, security/privacy design, production topology, migration, rollback, and material trade-offs.

## Exception Handling

- Stop when a design cannot meet an approved specification, ownership is missing, or migration/rollback is not credible.
- Record design alternatives and escalate required specification changes through `technology-specification-confirmation`.

## Handoff

Pass the approved design version, specification mapping, components, interfaces, deployment/observability/rollback work, risks, and review evidence to `technology-task-breakdown`.

## Example

Design an onboarding service architecture with components, data flow, observability, staged deployment, migration, health checks, and rollback mapped to fixed API and latency specifications.

## Common Mistakes

- Redefining specification thresholds inside the design
- Drawing components without responsibilities or data flow
- Omitting operations, migration, or rollback
