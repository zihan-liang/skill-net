---
name: technology-requirement
description: Use when a business need, product change, integration, infrastructure request, or operational problem needs a versioned, solution-neutral technology requirement; not for feasibility or specification approval.
---

# Technology Requirement

## Overview

Turn a business or operational need into a traceable, testable technology requirement without prematurely choosing a solution.

**中文摘要：** 将业务或运维需求整理为可追踪、可测试的技术需求，明确范围、功能、质量属性、依赖、风险和验收标准，避免过早锁定方案。

## Required Inputs

- Requester, owner, users, business outcome, urgency, and source references
- Current process/system, pain points, scope, exclusions, and affected environments
- Functional behavior, data, integrations, security/privacy, performance, reliability, and availability needs
- Constraints, dependencies, success measures, acceptance criteria, and approval route

## Workflow

1. Read `assets/technology_requirement_template.md`; assign `requirement_id` and version.
2. Confirm the problem, users, measurable outcome, owner, urgency, and evidence.
3. Separate functional requirements from performance, reliability, security, privacy, usability, and operability attributes.
4. Define inputs, outputs, data classification, interfaces, environments, dependencies, constraints, and exclusions.
5. Convert vague goals into observable acceptance criteria and success metrics.
6. Record assumptions, unknowns, conflicts, risks, and candidate discovery questions without inventing answers.
7. Route the baseline to business, product, technical, security, and data owners as applicable.

## Output Contract

Return:

- `requirement_id`, version, owner, users, business outcome, scope, and priority
- Functional requirements, quality attributes, data/interface needs, constraints, and dependencies
- Acceptance criteria, success metrics, assumptions, risks, evidence references, and missing information
- Review route and `status: draft`

## SkillNet Relationships

- Entry point for `technology-feasibility-assessment`.
- Supplies the approved baseline to design, task, test, release, and maintenance Skills.
- Passes confirmed versions through controlled, minimum-necessary records only after authorization.

## Approval Controls

- Do not invent users, system behavior, metrics, data classifications, constraints, or approvals.
- Keep the requirement solution-neutral unless a constraint has documented evidence.
- Human confirmation is required before baselining scope, priority, acceptance criteria, or change.

## Exception Handling

- Return for clarification when the owner, users, scope, environment, data classification, measurable outcome, or acceptance criteria are missing.
- Escalate conflicting stakeholder requirements and policy constraints without choosing a solution prematurely.

## Handoff

Pass the approved requirement ID/version, evidence, constraints, quality attributes, acceptance criteria, unknowns, and decision record to `technology-feasibility-assessment`.

## Example

Convert “make onboarding faster” into a versioned requirement with user journey, latency, availability, audit, privacy, integration, and measurable acceptance criteria.

## Common Mistakes

- Writing a chosen technology as the problem statement
- Mixing current facts, assumptions, and desired behavior
- Omitting non-functional requirements or affected environments
- Treating an unreviewed draft as the approved baseline
