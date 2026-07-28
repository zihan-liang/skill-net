---
name: procurement-contract-order
description: Use when an approved supplier selection needs a controlled contract draft, purchase-order draft, term reconciliation, approval routing, or release-readiness check.
---

# Procurement Contract and Order

## Overview

Translate an approved selection into traceable contract and purchase-order drafts while keeping legal acceptance, signature, and order release under human control.

**中文摘要：** 根据已批准的选商结果生成合同与采购订单草案，核对条款、金额和审批证据；不得自动签署、发送或下单。

## Required Inputs

- Approved selection, requirement, quote, budget, and decision evidence
- Supplier legal identity, items, quantities, prices, currency, tax/freight terms, and dates
- Delivery, warranty, service, data/security, acceptance, payment, remedy, and termination terms
- Contract/order IDs, approval matrix, authorized signatories, and source references

## Workflow

1. Preserve upstream IDs and reconcile the selected quote with the approved requirement and budget.
2. Identify standard terms, deviations, risks, owners, and required legal/security/finance review.
3. Draft the contract with scope, price, obligations, acceptance, change, remedy, confidentiality, and termination terms.
4. Read `assets/purchase_order_template.md`; require selection and order approval references.
5. Run `scripts/render_purchase_order.py` to calculate line totals and render a visibly unissued order.
6. Check contract/order consistency, supplier identity, dates, currency, quantities, and approval authority.
7. Route drafts for human legal acceptance, signature, and release; do not transmit them.

## Output Contract

Return contract/order IDs, linked source versions, draft terms, deviations, risk owners, approval route/evidence, rendered order, `contract_status: draft`, and `order_status: not_issued`.

## SkillNet Relationships

- Follows `procurement-supplier-selection`.
- Supplies the approved order to `procurement-delivery-acceptance`.
- Stores confirmed metadata through `procurement-supplier-database`.

## Guardrails

- Do not invent terms, approvals, signatories, tax treatment, or supplier identity.
- Do not provide jurisdiction-specific legal conclusions; route them to qualified counsel.
- Human approval is required for deviations, contract acceptance/signature, and order release.

## Example

Create a laptop supply contract draft and a CNY order marked NOT ISSUED after reconciling approved selection, price, warranty, delivery, and acceptance terms.

## Common Mistakes

- Copying a quote without reconciling requirement and selection versions
- Omitting remedies, acceptance, data/security, or change terms
- Rendering before both approval references exist
- Treating a draft as signed, sent, or issued
