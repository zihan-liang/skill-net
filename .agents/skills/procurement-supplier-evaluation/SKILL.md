---
name: procurement-supplier-evaluation
description: Use when completed deliveries or review periods need post-award supplier performance evaluation, improvement planning, or rating review; not for pre-award qualification, scoring, or selection.
---

# Procurement Supplier Evaluation

## Overview

Evaluate supplier performance with transparent weights and evidence coverage while reserving publication, renewal, suspension, and blacklisting decisions for authorized humans.

**中文摘要：** 基于交付、质量、服务、商务表现和合规证据评价供应商，展示评分与证据覆盖率；不得自动续约、停用或拉黑。

## Required Inputs

- `evaluation_id`, `supplier_id`, review period, contracts/orders, and delivery records
- Quality inspections, service incidents, corrective actions, commercial variances, and compliance evidence
- Authorized minimum invoice/payment-timeliness status from `finance-payment-approval` when commercial performance includes it
- Approved dimension weights, score definitions, reviewer identities, and conflict declarations
- Prior evaluation/improvement plan when trend comparison is required

## Workflow

1. Confirm the review period, supplier identity, scope, and complete delivery/contract population.
2. Separate observed evidence from reviewer interpretation; date every evidence reference.
3. Run `scripts/evaluate_supplier.py` on 0–5 delivery, quality, service, commercial-performance, and compliance dimensions.
4. Review missing evidence and coverage; do not fill gaps with assumptions or reputation.
5. Compare trends, recurring findings, corrective actions, and material incidents without hiding outliers.
6. Draft strengths, risks, improvement actions, owners, and deadlines proportionate to the evidence.
7. Route the evaluation for conflict-free human review and record any supplier response or appeal.

## Output Contract

Return evaluation/supplier IDs, period, weights, dimension scores/evidence, weighted score, coverage, performance band, trends, findings, improvement actions, supplier response, and `decision_status: human_review_required`.

## SkillNet Relationships

- Follows `procurement-delivery-acceptance` and the relevant `finance-payment-approval` evidence in the end-to-end procurement cycle.
- Feeds future `procurement-supplier-search`, `procurement-supplier-qualification`, and selection decisions.
- Remains distinct from pre-award `procurement-supplier-scoring`.

## Approval Controls

- Do not invent events, evidence, scores, reviewer consensus, or supplier responses.
- Do not use unrelated personal data or retaliatory criteria.
- Human approval is required for rating publication, improvement demands, renewal, suspension, or blacklisting.

## Exception Handling

- Mark missing evidence as missing, not zero; keep material incidents visible even when the average is high.
- Escalate reviewer conflicts, supplier appeals, suspected retaliation, or proposed suspension/blacklisting to authorized owners.

## Handoff

Pass the approved evaluation version, evidence coverage, material incidents, corrective actions, supplier response, and expiry/review date to future `procurement-supplier-search` and `procurement-supplier-qualification` work. Do not auto-renew or blacklist.

## Example

Evaluate a laptop supplier for Q3 using delivery, defect, support, price-variance, and compliance evidence, showing 80% coverage and an improvement action.

## Common Mistakes

- Scoring missing evidence as zero or five
- Averaging dimensions without disclosing weights and coverage
- Ignoring material incidents because the average is high
- Turning a performance band into an automatic supplier decision
