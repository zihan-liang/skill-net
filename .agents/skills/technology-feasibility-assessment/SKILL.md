---
name: technology-feasibility-assessment
description: Use when an approved technology requirement needs option comparison, prototype planning, dependency and risk analysis, estimates, or a go/no-go packet; not for specification confirmation or design.
---

# Technology Feasibility Assessment

## Overview

Assess whether and how a requirement can be delivered using dated evidence, explicit assumptions, comparable options, and reversible validation.

**中文摘要：** 从技术、运维、安全隐私、人员、周期、成本、依赖和迁移角度评估可行性，形成有证据的方案比较与人工立项建议。

## Required Inputs

- Approved requirement ID/version, acceptance criteria, priority, and constraints
- Current architecture, systems, data, interfaces, environments, capacity, and operational evidence
- Candidate build/buy/reuse options, team skills/capacity, schedule, cost range, and dependencies
- Security/privacy, compliance, licensing, vendor, migration, and support requirements

## Workflow

1. Read `assets/feasibility_assessment_template.md`; assign `feasibility_id`.
2. Verify the requirement baseline, sources, dates, unknowns, and decision deadline.
3. Define at least the status-quo and proposed options unless an exception is documented.
4. Assess each option across technical fit, operations, security/privacy, capacity, skills, schedule, cost, dependency, migration, reversibility, and support.
5. Distinguish measured facts, externally verified claims, estimates, and assumptions.
6. Design the smallest prototype or spike for high-impact unknowns, with success/failure criteria.
7. Compare options consistently; state risks, mitigations, confidence, evidence gaps, and recommendation.
8. Route the go/no-go, option, budget, and risk-acceptance decisions to authorized owners.

## Output Contract

Return `feasibility_id`, requirement version, options, dimension findings, evidence/assumptions, estimates/ranges, risks/mitigations, prototype plan/results, recommendation, confidence, missing information, and `decision_status: human_review_required`.

## SkillNet Relationships

- Blocks `technology-development-implementation` when `technology_not_feasible`.
- Part of `technology-agent`.
- Enhances `procurement-requirement` when `build_or_buy_decision`.
- Follows `technology-requirement`.
- Precedes `technology-specification-confirmation`.

## Approval Controls

- Do not invent benchmarks, system limits, costs, staffing, vendor claims, security findings, or approvals.
- Do not present a prototype as production proof or hide the status-quo option.
- Human approval is required for go/no-go, option selection, budget, security acceptance, and material risk acceptance.

## Exception Handling

- Mark untested claims, estimates, and assumptions separately; design a bounded spike for high-impact unknowns.
- Block recommendation when options are not comparable or security, migration, support, licensing, capacity, or cost evidence is materially missing.

## Handoff

Pass the human-approved option, feasibility version, evidence/assumptions, constraints, prototype results, risks, and open questions to `technology-specification-confirmation`.

## Example

Compare building, buying, and extending an onboarding platform using measured load, integration, privacy, staffing, migration, cost-range, and prototype evidence.

## Common Mistakes

- Using one preferred option as the only candidate
- Reporting point estimates without assumptions or ranges
- Ignoring operations, migration, security, licensing, or reversibility
- Treating a recommendation as an approved decision
