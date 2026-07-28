---
name: procurement-supplier-selection
description: Use when qualified supplier evidence and quote comparisons need to become a reviewable award recommendation, exception memo, or documented human selection decision.
---

# Procurement Supplier Selection

## Overview

Turn sourcing and quotation evidence into a consistent selection memo without converting a model score into an automatic award.

**中文摘要：** 基于供应商资质、报价比较、风险与利益冲突证据形成选商建议；最终选择和例外批准必须由授权人员决定。

## Required Inputs

- Approved requirement, budget confirmation, sourcing shortlist, and quote comparison
- Qualification/due-diligence evidence, commercial terms, risks, and evidence dates
- Conflict declarations, evaluation weights, exception policy, and approval matrix
- Single-source justification or dissenting reviewer comments when applicable

## Workflow

1. Read `assets/supplier_selection_memo.md`; assign `selection_id` and preserve upstream IDs.
2. Verify each considered supplier passed mandatory requirements or has a documented exception.
3. Reconcile quote totals, ranking, commercial terms, due diligence, risks, and evidence currency.
4. Compare price, quality, delivery, service, capacity, compliance, and lifecycle value consistently.
5. Surface conflicts, concentration risk, weak evidence, deviations, and negotiation conditions.
6. State one recommendation with alternatives and rationale; record dissent without suppressing it.
7. Route the memo to conflict-free approvers and keep `award_status` pending until evidence is received.

## Output Contract

Return:

- `selection_id`, upstream IDs/versions, suppliers considered, and decision criteria
- Evidence matrix, quote results, due-diligence findings, risks, exceptions, and conflicts
- Recommended supplier and alternatives with traceable rationale and dissent
- Approval route, decision evidence, and `award_status: human_review_required`

## SkillNet Relationships

- Follows `procurement-quote-comparison`.
- Supplies an approved selection to `procurement-contract-order`.
- Persists confirmed decisions through `procurement-supplier-database`.

## Guardrails

- Do not invent evidence, alter weights after seeing results, or hide exceptions or dissent.
- Do not treat lowest price, incumbency, or highest score as sufficient by itself.
- Human approval is required for selection, single-source exceptions, negotiation, and award communication.

## Example

Recommend a laptop supplier after reconciling score, warranty, delivery, security evidence, conflict checks, and a documented exception for one late bid.

## Common Mistakes

- Awarding directly from the rank column
- Changing criteria after quotes are opened
- Ignoring conflicts, concentration risk, or total lifecycle cost
- Recording a recommendation as an approved award
