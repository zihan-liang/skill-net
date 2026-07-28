---
name: procurement-delivery-acceptance
description: Use when goods or services delivered against a purchase order need quantity, timing, condition, quality, documentation, or acceptance checks and a discrepancy record.
---

# Procurement Delivery Acceptance

## Overview

Compare delivered goods or services with the approved order and acceptance criteria, keeping observed facts separate from the authorized acceptance decision.

**中文摘要：** 对照合同和订单检查交付数量、时间、状态、质量与文件，记录差异和证据；最终验收、拒收或例外接收由授权人员决定。

## Required Inputs

- Approved contract/order IDs, versions, lines, delivery terms, and acceptance criteria
- Supplier/delivery IDs, dispatch and receipt dates, receiver, and location
- Packing list, serial/batch data, service milestones, inspection/test evidence, and photos/references
- Tolerance, partial-delivery, quarantine, return, remedy, and approval policies

## Workflow

1. Read `assets/delivery_acceptance_template.md`; assign `delivery_id` and link the exact order version.
2. Verify supplier, location, delivery date, packing/service documents, and receiver identity.
3. Compare ordered, delivered, previously accepted, damaged, and remaining quantities line by line.
4. Test measurable quality, functional, security, documentation, and service criteria.
5. Record each shortage, excess, defect, delay, or document gap with evidence and severity.
6. Recommend accept, accept with exception, quarantine, rework, return, or reject; do not execute the action.
7. Route the record to the authorized owner and preserve supplier acknowledgement and corrective-action references.

## Output Contract

Return:

- `delivery_id`, supplier/order/contract IDs, dates, receiver, and location
- Line reconciliation, inspection checks, evidence references, discrepancies, and severity
- Recommended disposition, corrective actions, responsible owners, and deadlines
- Human decision evidence and `acceptance_status: human_review_required`

## SkillNet Relationships

- Follows `procurement-contract-order`.
- Supplies evidence to `procurement-supplier-evaluation` and finance invoice/payment checks.
- Persists confirmed delivery records through `procurement-supplier-database`.

## Guardrails

- Do not invent inspection results, signatures, delivery dates, quantities, defects, or remedies.
- Do not overwrite the original order or evidence when correcting a receipt.
- Human approval is required for acceptance, exception, quarantine, return, rejection, or remedy release.

## Example

Inspect 20 laptops against the approved order, record 19 received and one damaged unit with serial/photo evidence, and route a partial-acceptance recommendation.

## Common Mistakes

- Treating a packing list as proof of quality or receipt
- Omitting prior partial deliveries or accepted quantities
- Recording a recommendation as the final acceptance decision
- Losing evidence links when a discrepancy is corrected
