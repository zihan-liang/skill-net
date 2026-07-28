---
name: procurement-delivery-acceptance
description: Use when arrived goods or completed services need quantity, condition, quality, document, and acceptance-criteria checks; not for delivery tracking, invoice verification, or payment approval.
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

- Follows `procurement-delivery-tracking` and uses the released `procurement-purchase-order` version.
- Supplies evidence to `finance-invoice-verification` and `procurement-supplier-evaluation`.
- Does not verify invoices or authorize payment.

## Approval Controls

- Do not invent inspection results, signatures, delivery dates, quantities, defects, or remedies.
- Do not overwrite the original order or evidence when correcting a receipt.
- Human approval is required for acceptance, exception, quarantine, return, rejection, or remedy release.

## Exception Handling

- Quarantine or hold the recommendation when ordered and delivered identities conflict, inspection evidence is missing, or safety/security defects exist.
- Preserve original receipt and inspection evidence; corrections use a versioned record and append-only audit reference.

## Handoff

Pass the PO/delivery IDs, line reconciliation, human acceptance evidence/status, discrepancies, remedies, and evidence references to `finance-invoice-verification` and later `procurement-supplier-evaluation`. Never label an invoice payable.

## Example

Inspect 20 laptops against the approved order, record 19 received and one damaged unit with serial/photo evidence, and route a partial-acceptance recommendation.

## Common Mistakes

- Treating a packing list as proof of quality or receipt
- Omitting prior partial deliveries or accepted quantities
- Recording a recommendation as the final acceptance decision
- Losing evidence links when a discrepancy is corrected
