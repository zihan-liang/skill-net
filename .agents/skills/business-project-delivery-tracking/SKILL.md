---
name: business-project-delivery-tracking
description: Use when a signed customer project needs contract-linked milestone, change, blocker, risk, and delivery-status tracking; not for customer acceptance or renewal.
---

# Business Project Delivery Tracking

## Overview

Track contract-linked delivery using owned, weighted, evidence-backed milestones without inventing progress, changing scope, or claiming customer acceptance.

**中文摘要：** 按合同和里程碑跟踪项目交付、完成度、证据、逾期、阻塞、变更与风险；不得虚构进度、擅改范围或代替客户验收。

## Required Inputs

- Contract/project/customer IDs and versions, delivery owner, reporting date, scope, deliverables, and acceptance criteria
- Milestone IDs, title, owner, weight, due date, status, progress, dependency, and evidence
- Approved changes, decisions, blockers, risks, budget/resource constraints, communications, and escalation route
- Customer responsibilities, review windows, service levels, invoice/payment dependencies, and data/security constraints

## Workflow

1. Read `assets/project_delivery_tracker.md`; preserve contract, quotation, project, and change traceability.
2. Decompose only the contracted delivery into uniquely identified milestones whose approved weights total 100.
3. For each reporting cycle, collect owner evidence, progress, dates, dependencies, blockers, risks, and customer decisions.
4. Run `scripts/evaluate_delivery_progress.py`; inspect weighted completion, overdue work, blocked work, inconsistencies, and missing completion evidence.
5. Reconcile approved changes with scope, schedule, cost, acceptance, responsibilities, and downstream contract or quotation versions.
6. Forecast impacts as assumptions with evidence; distinguish internal completion, delivery, customer review, and acceptance.
7. Define recovery actions, owners, due dates, escalation thresholds, and customer communication proposals.
8. Route scope, schedule, commercial, delivery claim, customer communication, and closure decisions to authorized humans.

## Output Contract

Return contract/project IDs, reporting date, milestone table, weighted completion, evidence, overdue/blocked findings, changes, risks, recovery actions, owners, decisions, `delivery_status`, and external communication state.

## SkillNet Relationships

- Part of `business-agent`.
- Follows `business-contract-signing`.
- Precedes `business-acceptance`.

## Approval Controls

- Do not invent progress, evidence, forecast certainty, delivery, acceptance, customer decisions, or payment status.
- Do not alter scope, deadlines, resources, contract terms, or customer messages outside explicit authority.
- Human approval is required for change requests, delivery claims, customer escalation, milestone closure, and database mutation.

## Exception Handling

- Escalate unapproved scope change, missing completion evidence, blocked/overdue critical milestones, customer dependency failure, or contract-version conflict.
- Preserve original milestones and approved changes; do not overwrite adverse status or infer acceptance from completion.

## Handoff

Pass contract/project/change versions, deliverables, milestone evidence, approved delivery claims, open blockers, customer observations, acceptance criteria, and owners to `business-acceptance`; do not mark customer acceptance.

## Example

Evaluate three onboarding milestones weighted 40/35/25, compute 57.50% completion, and escalate an evidenced blocker without claiming customer acceptance.

## Common Mistakes

- Reporting activity instead of contract-linked outcomes
- Marking complete without evidence or acceptance distinction
- Hiding overdue or blocked milestones in an average
- Applying scope changes without approved version traceability
