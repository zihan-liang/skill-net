---
name: business-renewal
description: Use when an accepted customer contract approaches renewal and needs renewal evaluation, options, scope and price proposal, quotation, or follow-up tracking; not for acceptance or contract signature.
---

# Business Renewal

## Overview

Evaluate renewal value and risk, prepare versioned renewal options and pricing, and track authorized follow-up without promising renewal.

**中文摘要：** 负责续约评估、续约方案、报价和续约跟踪；不负责业务验收或合同签署。

## Required Inputs

- Customer/contract/acceptance/renewal IDs, contract term, notice/renewal windows, owners, and evidence
- Verified outcomes, usage/adoption, satisfaction, service performance, incidents, obligations, and open issues
- Payment status reference from finance, delivery capacity, scope/price/cost inputs, policy, authority, and customer-contact route

## Workflow

1. Read `assets/renewal_template.md`; assign `renewal_id` and preserve source versions.
2. Verify acceptance status, contract dates, notice obligations, customer relationship, and evidence cutoff.
3. Assess outcomes, adoption, satisfaction, service, open obligations, risk, strategic fit, delivery capacity, and payment evidence without inferring intent.
4. Prepare no-renewal, like-for-like, expansion, reduction, or remediation options as applicable.
5. Build versioned scope and quotation assumptions using approved commercial inputs; identify approvals and dependencies.
6. Define owners, timeline, authorized contact plan, follow-up cadence, decision checkpoints, and status evidence.
7. Route pricing, offer, customer message, negotiation, and final renewal decisions to authorized humans.

## Output Contract

Return renewal/customer/contract IDs, window/dates, evidence cutoff, value/risk assessment, options, proposed scope and quotation, assumptions, approvals, owners, follow-up plan/history, and `renewal_status: human_review_required`.

## SkillNet Relationships

- Blocked by `business-acceptance` when `business_acceptance_failed`.
- Part of `business-agent`.
- Follows `business-acceptance`.

## Approval Controls

- Use minimum customer/contact data, stable IDs, restricted references, actor/purpose, versioned offers, and append-only communication/status history.
- Stored status, satisfaction, or payment evidence is not proof of renewal intent or agreement.
- Do not invent usage, outcomes, feedback, prices, capacity, intent, approval, contact, or agreement.
- Human approval is required for pricing, offer release, contact, concession, negotiation, renewal, non-renewal, and final status.

## Exception Handling

- Escalate missing acceptance, disputed outcomes, overdue obligations, payment disputes, capacity gaps, missed notice windows, or conflicting customer signals.
- Keep assumptions and unresolved risks visible; do not convert positive satisfaction into a forecast commitment.

## Handoff

Pass the approved renewal option/version, quotation, assumptions, decision mandate, customer-contact approval, open risks, and evidence to `business-negotiation`; route final terms to contract signing only after human agreement.

## Example

Assess a merchant contract 90 days before expiry, prepare like-for-like and expansion quotations, and track approved follow-up without promising renewal.

## Common Mistakes

- Combining acceptance and renewal
- Inferring renewal intent from satisfaction or payment
- Sending unapproved pricing or recording a forecast as agreement
