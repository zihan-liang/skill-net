---
name: business-acceptance
description: Use when customer deliverables need contract-criteria checks, exception and remedy handling, customer review, or sign-off preparation; not for delivery tracking, invoicing, payment, or renewal.
---

# Business Acceptance

## Overview

Compare delivered outcomes with contractual acceptance criteria and prepare an evidence-complete customer sign-off packet. Internal completion is not customer acceptance.

**中文摘要：** 负责交付物检查、异常处理和客户签署准备；不负责项目跟踪、发票付款或续约。

## Required Inputs

- Customer/contract/project/deliverable/acceptance IDs and versions
- Contract acceptance criteria, approved changes, delivery/test evidence, customer review window, and owners
- Customer observations, exceptions, remedies, authority evidence, and communication route

## Workflow

1. Read `assets/acceptance_template.md`; preserve contract, project, change, deliverable, and evidence versions.
2. Map every contractual criterion to delivered evidence and mark pass, fail, exception, or not evidenced.
3. Distinguish internal completion, delivery, customer review, and customer acceptance.
4. Record customer observations, defects, exceptions, remedies, owners, due dates, and retest evidence.
5. Verify sign-off authority, document version/digest, review window, and open dependencies.
6. Draft the acceptance or exception packet and customer message; do not send or sign.
7. Record accepted/rejected/conditional status only from verified customer evidence.

## Output Contract

Return linked IDs/versions, criterion/evidence matrix, delivered items, exceptions, remedies, owners/dates, customer observations, sign-off route, document digest, `acceptance_status`, and `external_action: not_performed`.

## SkillNet Relationships

- Follows `business-project-delivery-tracking` and precedes `business-renewal` after verified acceptance evidence.
- May supply acceptance evidence to `finance-invoice-verification` without issuing an invoice.
- Does not evaluate renewal value or prepare renewal pricing.

## Approval Controls

- Use stable IDs, minimum customer data, restricted evidence/document references, actor/purpose, versions, and append-only audit history.
- Stored status is not proof of delivery, customer acceptance, or signature.
- Do not invent customer feedback, acceptance, authority, signature, date, or communication.
- Human approval and customer authority are required for exceptions, remedies, sign-off, external messages, and final status.

## Exception Handling

- Block sign-off when criteria lack evidence, versions conflict, authority is missing, or material defects/remedies remain unresolved.
- Preserve superseded packets and customer objections; never overwrite adverse evidence or convert silence to acceptance unless the contract and authorized reviewer confirm it.

## Handoff

Pass verified acceptance evidence, unresolved obligations, customer observations, outcome evidence, contract dates, and responsible owners to `business-renewal`; separately pass finance only the approved minimum acceptance reference.

## Example

Map five onboarding deliverables to contract criteria, record one customer exception and remedy, and prepare an unsigned acceptance packet.

## Common Mistakes

- Treating internal completion as customer acceptance
- Hiding exceptions or missing evidence
- Signing or messaging without authority
