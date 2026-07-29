---
name: procurement-contract-generation
description: Use when an approved supplier selection needs contract terms, version control, deviation review, legal or finance approval routing, and signature preparation; not for creating or releasing a PO.
---

# Procurement Contract Generation

## Overview

Translate an approved supplier selection into a controlled contract draft. Signature and legal acceptance remain human actions.

**中文摘要：** 根据选商结果生成合同条款与版本，完成偏差和审批准备；不生成采购订单，也不自动签署。

## Required Inputs

- Human-approved selection, requirement, scorecard, quote, budget check, and decision evidence
- Supplier legal identity and approved scope, price, currency, dates, delivery, acceptance, payment, warranty, remedy, security/privacy, and termination terms
- Contract ID, standard template/version, deviation matrix, reviewers, signatories, and authority evidence

## Workflow

1. Read `assets/contract_draft_template.md`; assign `contract_id` and version.
2. Reconcile the selected supplier and approved commercial basis with upstream versions.
3. Draft scope, obligations, delivery, acceptance, change, payment, warranty, remedy, confidentiality, data/security, IP, liability, termination, and dispute terms.
4. Identify every deviation from standard terms with risk, owner, and required approval.
5. Verify legal entity, dates, currency, total/value basis, signatory authority, and separation of duties.
6. Route business, legal, finance, security/privacy, and executive review as required.
7. Freeze the approved document digest for signature; do not sign, send, or mark executed.

## Output Contract

Return contract/selection IDs and versions, immutable digest, terms, deviation/risk matrix, reviewer findings, signatory route, evidence gaps, `contract_status: draft`, and `signature_status: pending`.

## SkillNet Relationships

- Blocked by `procurement-supplier-qualification` when `supplier_not_qualified`.
- Part of `procurement-agent`.
- Follows `business-negotiation`.
- Precedes `procurement-purchase-order`.

## Approval Controls

- Store restricted references and digests rather than full confidential contracts in open records; preserve stable IDs, actor/purpose, versions, and audit history.
- Do not invent terms, legal identity, authority, approval, signature, or execution status.
- Human approval is required for terms, deviations, legal acceptance, signature, transmission, and execution status.

## Exception Handling

- Stop on version/digest mismatch, unresolved material deviation, missing authority, inconsistent supplier identity, or conflict with approved scope or price.
- Route jurisdiction-specific conclusions to qualified counsel and preserve superseded versions.

## Handoff

After verified human execution, pass the contract ID/version/digest, execution evidence, supplier, scope, commercial terms, delivery/acceptance obligations, and restrictions to `procurement-purchase-order`.

## Example

Draft a laptop supply contract from an approved selection and freeze its SHA-256 digest after legal and finance review, with signature still pending.

## Common Mistakes

- Combining contract drafting with PO generation
- Omitting remedies, data/security, change, or acceptance terms
- Treating approval readiness as signature
