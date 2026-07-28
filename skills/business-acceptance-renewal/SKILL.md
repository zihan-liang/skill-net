---
name: business-acceptance-renewal
description: Use when customer deliverables need acceptance review, exception handling, sign-off preparation, outcome review, payment follow-up context, renewal assessment, or renewal-plan preparation.
---

# Business Acceptance and Renewal

## Overview

Prepare evidence-based customer acceptance and renewal decisions while keeping sign-off, collection action, commercial offers, and renewal commitments under human authority.

**中文摘要：** 对照合同验收标准核对交付与例外，整理签署和回款依据，并评估续约价值、风险与下一步；不得代替客户验收、催款或承诺续约条件。

## Required Inputs

- Customer/contract/project/deliverable/acceptance IDs, versions, owners, dates, and evidence
- Contract acceptance criteria, delivered outcomes, test/delivery evidence, customer review, exceptions, remedies, and sign-off authority
- Invoice/payment references and statuses, disputes, dependencies, communication authority, and finance evidence
- Renewal date/window, usage/outcome evidence, customer feedback, service performance, open issues, pricing/capacity inputs, and decision authority

## Workflow

1. Read `assets/acceptance_renewal_template.md`; preserve contract, project, change, delivery, and evidence versions.
2. Compare every contractual acceptance criterion with delivered evidence; mark pass, fail, exception, or not evidenced.
3. Record customer observations, exceptions, remedies, owners, due dates, review window, and proposed sign-off route.
4. Distinguish internal completion, customer delivery, customer acceptance, invoice eligibility, invoice issuance, and payment receipt.
5. Verify payment status only from finance evidence; route disputes, reminders, credits, or collection proposals to authorized humans.
6. Assess renewal using outcomes, adoption, satisfaction, support/service evidence, unresolved risks, strategic fit, delivery capacity, and commercial inputs.
7. Prepare options, assumptions, pricing or scope dependencies, approval needs, owners, timing, and an authorized customer-contact plan.
8. Record acceptance or renewal status only from verified decisions; retain exceptions and superseded versions.

## Output Contract

Return linked IDs, criterion/evidence matrix, exceptions/remedies, sign-off route/status, payment evidence/status, renewal window, outcome/value assessment, risks, options, approvals, owners, next steps, `acceptance_status`, and `renewal_status`.

## SkillNet Relationships

- Follows `business-project-delivery-tracking` and closes or restarts the business cycle.
- Shares payment evidence with finance without executing accounting or collection.
- Stores confirmed acceptance, payment, and renewal metadata through `business-customer-database`.

## Guardrails

- Do not invent acceptance, customer feedback, usage, outcomes, invoice, payment, satisfaction, renewal intent, or approval.
- Do not sign for a customer, issue an invoice, collect funds, contact a customer, or offer renewal terms without authority.
- Human approval is required for acceptance, exceptions, remedies, collection action, pricing, renewal offer, and final status.

## Example

Compare a merchant onboarding delivery with five criteria, record one accepted exception, cite payment evidence, and prepare two renewal options for human review.

## Common Mistakes

- Treating internal completion as customer acceptance
- Hiding exceptions or missing evidence in a summary status
- Inferring payment from an invoice or renewal from satisfaction
- Contacting the customer before approving the message and terms
