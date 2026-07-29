---
name: procurement-supplier-selection
description: Use when qualification, commercial comparison, and supplier scores need an award recommendation or selection decision packet; not for scoring, contracting, or order release.
---

# Procurement Supplier Selection

## Overview

Turn sourcing and quotation evidence into a consistent selection memo without converting a model score into an automatic award.

**中文摘要：** 基于供应商资质、报价比较、风险与利益冲突证据形成选商建议；最终选择和例外批准必须由授权人员决定。

## Required Inputs

- Approved requirement, finance budget check, qualification results, quote comparison, and supplier scorecard
- Qualification/due-diligence evidence, commercial terms, risks, and evidence dates
- Conflict declarations, evaluation weights, exception policy, and approval matrix
- Single-source justification or dissenting reviewer comments when applicable

## Workflow

1. Read `assets/supplier_selection_memo.md`; assign `selection_id` and preserve upstream IDs/versions.
2. Verify each considered supplier passed mandatory requirements or has a documented exception.
3. Reconcile quote totals, ranking, commercial terms, due diligence, risks, and evidence currency.
4. Reconcile the pre-approved scorecard with price, quality, delivery, capacity, compliance, risk, and lifecycle value.
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

- Blocked by `procurement-supplier-qualification` when `supplier_not_qualified`.
- Part of `procurement-agent`.
- Follows `procurement-supplier-scoring`.
- Precedes `business-negotiation`.

## Approval Controls

- Do not invent evidence, alter weights after seeing results, or hide exceptions or dissent.
- Do not treat lowest price, incumbency, or highest score as sufficient by itself.
- Human approval is required for selection, single-source exceptions, negotiation, and award communication.

## Exception Handling

- Stop when mandatory qualification failed, scoring evidence is incomplete, versions conflict, or decision-makers have unresolved conflicts.
- Record ties, dissent, single-source justification, and deviations; do not alter criteria to force a preferred result.

## Handoff

Pass the signed decision reference, selected supplier ID, approved commercial basis, exceptions, risks, negotiation conditions, and source versions to `procurement-contract-generation`; keep `award_status` pending until evidence exists.

## Example

Recommend a laptop supplier after reconciling score, warranty, delivery, security evidence, conflict checks, and a documented exception for one late bid.

## Common Mistakes

- Awarding directly from the rank column
- Changing criteria after quotes are opened
- Ignoring conflicts, concentration risk, or total lifecycle cost
- Recording a recommendation as an approved award
