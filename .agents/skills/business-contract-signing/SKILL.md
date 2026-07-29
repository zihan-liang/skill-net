---
name: business-contract-signing
description: Use when a negotiated customer contract needs version reconciliation, approval routing, signatory-authority review, signature readiness, or execution evidence; not for negotiation or project delivery.
---

# Business Contract Signing

## Overview

Validate that the intended contract version, parties, approvals, authority, deviations, and required terms are ready for authorized human signature.

**中文摘要：** 核验合同版本、文件指纹、双方主体、签署权限、审批、谈判偏差和关键条款；仅判断是否可进入人工签署，不自动签署或发送。

## Required Inputs

- Contract/customer/opportunity/quotation IDs, approved source versions, contract version, immutable document digest, owner, and evidence
- Legal counterparties, registration references, notices, addresses, authorized signatories, and authority evidence
- Required business, finance, legal, privacy, security, tax, or executive approvals and separation-of-duty rules
- Negotiated deviations and required scope, pricing, delivery, acceptance, payment, confidentiality, data/security, IP, liability, change, termination, and dispute terms

## Workflow

1. Read `assets/contract_signing_checklist.md`; identify the exact contract file and SHA-256 digest.
2. Reconcile contract scope, price, currency, dates, deliverables, and acceptance with approved opportunity, quotation, and negotiation versions.
3. Verify each legal party, signatory identity, role, authority reference, signature method, and required execution sequence.
4. Confirm required approvals are approved, evidenced, current, and issued for this contract version.
5. Resolve every negotiated deviation and inspect the required commercial, delivery, risk, data, IP, liability, termination, and dispute terms.
6. Run `scripts/validate_contract_signing.py`; stop on every blocking finding.
7. Route the immutable packet to authorized humans; independently verify returned signature and execution evidence.
8. Record signed status only from verified evidence and store restricted references rather than the full contract.

## Output Contract

Return linked IDs, contract version/digest, parties, signatories, approvals, deviation and term findings, readiness, signature route, evidence needs, `signature_status`, and `external_action`.

## SkillNet Relationships

- Part of `business-agent`.
- Follows `business-negotiation`.
- Precedes `business-project-delivery-tracking`.

## Approval Controls

- Do not invent legal identity, authority, approval, term, signature, date, or execution status.
- Do not give jurisdiction-specific legal conclusions or upload full contracts to unrestricted stores.
- Human approval is required for terms, deviations, signature, transmission, execution status, and database mutation.

## Exception Handling

- Stop on digest/version mismatch, missing approval, unresolved deviation, uncertain legal entity, or absent signatory authority.
- Preserve superseded versions and route jurisdiction-specific legal conclusions to qualified counsel.

## Handoff

After independently verified execution, pass contract/customer IDs, exact version/digest, signed evidence reference, scope, milestones, acceptance, payment, change terms, risks, and owners to `business-project-delivery-tracking`.

## Example

Validate version 3 of a merchant-service agreement using its SHA-256 digest, two authorized signatories, business/legal/finance approvals, resolved deviations, and required-term references.

## Common Mistakes

- Signing a file whose digest differs from the approved version
- Assuming a job title proves signature authority
- Leaving negotiated changes out of the final contract
- Treating readiness validation as signature or execution
