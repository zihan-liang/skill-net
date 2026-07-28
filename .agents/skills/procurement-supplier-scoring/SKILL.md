---
name: procurement-supplier-scoring
description: Use when qualified suppliers need an evidence-backed pre-award score across qualification, price, delivery, quality, and risk; not for quote normalization, selection, or post-delivery evaluation.
---

# Procurement Supplier Scoring

## Overview

Create a transparent pre-award scorecard from qualification and quotation evidence. A rank is decision support, not an award.

**中文摘要：** 综合资质、价格、交付、质量与风险形成供应商评分表；与报价标准化和最终选商分离。

## Required Inputs

- Qualification outputs, normalized quote comparison, request/RFQ versions, and supplier IDs
- Approved 0–5 dimension definitions, weights, evidence dates, reviewer identities, and conflicts
- Delivery capability, quality evidence, risk findings, and exception policy

## Workflow

1. Read `assets/supplier_scorecard.md`; assign `scoring_id` and freeze input versions.
2. Confirm weights and score definitions were approved before results were reviewed.
3. Cite evidence for qualification, price, delivery, quality, and risk for each supplier.
4. Encode the scorecard as JSON and run `scripts/score_suppliers.py`.
5. Keep missing, expired, conflicting, or exception evidence visible and affected suppliers unranked.
6. Review calculations, evidence coverage, material risks, conflicts, and sensitivity to weights.
7. Route the scorecard to authorized reviewers without naming a winner.

## Output Contract

Return scoring/request/RFQ IDs, weights/definitions, supplier dimension evidence, weighted scores, eligibility, blocking findings, ranking, conflicts, exceptions, and `decision_status: human_review_required`.

## SkillNet Relationships

- Follows `procurement-quote-comparison` and consumes `procurement-supplier-qualification` evidence.
- Precedes `procurement-supplier-selection`.
- Is pre-award analysis; post-delivery performance belongs to `procurement-supplier-evaluation`.

## Approval Controls

- Do not invent scores, evidence, consensus, or weight approval; never change weights after seeing results without a versioned approval.
- Keep stable supplier IDs, minimum fields, restricted evidence references, actor/purpose, and append-only scoring/audit history.
- Human approval is required for weights, exceptions, final scorecard, and use in an award decision.

## Exception Handling

- Do not rank a supplier with failed mandatory qualification, missing evidence, unknown identity, or an unapproved exception.
- Escalate ties, conflicting evidence, material risk, reviewer conflict, or non-comparable scope without manufacturing precision.

## Handoff

Pass the scorecard version, full evidence matrix, exclusions, exceptions, risks, and human review status to `procurement-supplier-selection`; do not report selection or award.

## Example

Score three laptop suppliers using approved 20/30/20/20/10 weights and leave one supplier unranked for missing quality evidence.

## Common Mistakes

- Repeating price normalization in this stage
- Using evidence-free quality or risk scores
- Treating rank one as an automatic award
