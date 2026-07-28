---
name: technology-solution-design
description: Use when an approved technology requirement and feasibility decision need architecture, component, data-flow, interface, security, capacity, observability, deployment, or rollback design.
---

# Technology Solution Design

## Overview

Produce a reviewable technical design that maps every major decision and component to requirements, evidence, risks, operations, and reversibility.

**中文摘要：** 将已批准的技术需求与可行性结论转化为技术方案，明确架构、组件、数据流、接口、安全、容量、可观测性、部署和回滚设计。

## Required Inputs

- Approved requirement and feasibility IDs/versions, chosen option, constraints, and decision evidence
- Current architecture/systems, data classification, interfaces, environments, and ownership
- Quality attributes, traffic/capacity assumptions, failure modes, security/privacy controls, and standards
- Deployment, migration, observability, backup/recovery, rollback, testing, and review policies

## Workflow

1. Read `assets/technical_design_template.md`; assign `design_id` and version.
2. Preserve requirement traceability and identify assumptions, unknowns, exclusions, and measurable design targets.
3. Define system context, components, responsibilities, dependencies, data ownership/flow, storage, and interfaces.
4. Specify authentication/authorization, secrets handling, encryption, privacy, threat controls, and auditability.
5. Size capacity, concurrency, latency, availability, resilience, backup/recovery, and cost assumptions.
6. Design logs, metrics, traces, alerts, service objectives, operational ownership, and runbooks.
7. Define build/buy boundaries, environments, migration, compatibility, deployment, health checks, rollback, and failure recovery.
8. Record alternatives, trade-offs, architecture decisions, risks, verification plan, and required reviewers.

## Output Contract

Return `design_id`, version, linked decisions, context/components, data flows, interfaces, security controls, capacity/resilience, observability, deployment/migration/rollback, decisions/trade-offs, test plan, risks, sources, reviewers, and `status: draft`.

## SkillNet Relationships

- Follows `technology-feasibility-assessment` and precedes `technology-task-breakdown`.
- Supplies design targets to implementation, test, release, and operations Skills.
- Persists approved design metadata through `technology-database`.

## Guardrails

- Do not invent system state, benchmarks, security guarantees, compatibility, capacity, or review evidence.
- Do not include secrets, credentials, customer data, or proprietary source bodies.
- Human approval is required for architecture, security/privacy acceptance, migration, production topology, and material trade-offs.

## Example

Design an onboarding service with explicit APIs, data ownership, 95th-percentile latency, availability, access controls, audit events, observability, migration, and rollback.

## Common Mistakes

- Drawing components without responsibilities or requirement links
- Omitting failure modes, operations, migration, or rollback
- Treating estimates as measured capacity
- Claiming architecture or security approval without evidence
