---
name: procurement-purchase-order
description: Use when an approved procurement contract needs a purchase-order draft, line and total validation, approval routing, release control, or PO status record; not for drafting contract terms.
---

# Procurement Purchase Order

## Overview

Generate a contract-linked PO and keep approval, release, supplier transmission, and status changes under explicit human authority.

**中文摘要：** 根据已批准合同生成采购订单，校验 PO 内容、审批、释放和状态记录；不负责合同条款设计。

## Required Inputs

- Approved contract ID/version/digest and human execution evidence
- Supplier ID, ship/bill details, line items, quantities, unit prices, currency, tax/freight, dates, and delivery milestones
- PO ID, requester/buyer/approvers, threshold policy, release authority, and source references

## Workflow

1. Read `assets/purchase_order_template.md`; assign `order_id` and preserve contract/selection references.
2. Reconcile supplier, scope, quantities, prices, currency, taxes, freight, delivery, acceptance, and payment terms to the approved contract.
3. Encode the PO data and run `scripts/render_purchase_order.py`.
4. Verify totals, dates, unique line IDs, approval thresholds, requester/buyer/approver separation, and duplicate PO indicators.
5. Render the document visibly as not issued until approval evidence is received.
6. Route approval and release to authorized humans; do not transmit to the supplier.
7. Record release/status only from external evidence using a stable ID and append-only audit reference.

## Output Contract

Return order/contract/selection IDs and versions, normalized lines/totals, delivery and payment terms, validation findings, approval route/evidence, audit reference, `order_status: not_issued`, and `external_action: not_performed`.

## SkillNet Relationships

- Follows `procurement-contract-generation` and precedes `procurement-delivery-tracking` after authorized release.
- Supplies PO evidence to delivery acceptance and finance invoice verification.
- Does not change contract terms; discrepancies return to contract generation.

## Approval Controls

- Use stable IDs, allowlisted minimum fields, restricted document references, actor/purpose, and immutable/append-only change evidence.
- Database status is not proof of approval, release, or supplier receipt.
- Human approval is required for PO approval, release, amendment, cancellation, transmission, and status correction.

## Exception Handling

- Stop on contract/PO mismatch, duplicate order, missing execution evidence, invalid totals, unauthorized threshold route, or supplier identity conflict.
- Use a versioned amendment or cancellation route; never overwrite an issued PO or fabricate supplier acknowledgement.

## Handoff

After verified release and supplier acknowledgement, pass PO version, lines, milestones, contacts, approval/release evidence, and open issues to `procurement-delivery-tracking`.

## Example

Render a 20-laptop CNY PO linked to a signed contract, leaving it marked NOT ISSUED until buyer approval and release evidence exist.

## Common Mistakes

- Drafting new legal terms inside the PO
- Treating rendering as issuance
- Recording release without external evidence
