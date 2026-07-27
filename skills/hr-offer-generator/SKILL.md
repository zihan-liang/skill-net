---
name: hr-offer-generator
description: Use when an approved finalist needs compensation validation, a draft offer letter, offer-version tracking, acceptance monitoring, or an employment-offer review package.
---

# HR Offer Generator

## Overview

Validate approved employment terms and produce a traceable draft offer. Keep compensation, role, dates, and signatory authority aligned with the final hiring decision.

**中文摘要：** 校验薪资与录用审批，生成Offer草案并跟踪版本及候选人状态。

## Required Inputs

- Approved finalist and interview decision
- Approved role, level, department, manager, and location
- Approved compensation, benefits, employment type, and probation terms
- Start date, acceptance deadline, company entity, and authorized signatory

## Workflow

1. Confirm final-selection, compensation, and offer approvals with their owners and timestamps.
2. Compare the proposed terms with the approved role and compensation range; stop on any mismatch.
3. Read `assets/offer_template.md` and prepare a JSON value for every placeholder.
4. Run `scripts/generate_offer.py` to reject missing fields and produce the draft.
5. Review entity, dates, currency, pay period, location, probation, benefits, contingencies, and signatory.
6. Assign a version, approval record, expiry date, and status.
7. Present the draft for authorized signature and external-send confirmation; never send it automatically.

## Output Contract

Return:

- `candidate_id`, `request_id`, and `offer_version`
- `validation_checks` and `approval_evidence`
- `draft_offer_path` or `draft_offer_text`
- `acceptance_deadline`
- `signature_status`, `send_status`, and `candidate_status`

## SkillNet Relationships

- Requires an approved finalist from `hr-interview-scheduling`.
- Precedes `hr-onboarding` after signed acceptance.
- Conflicts with generation when compensation or offer approval is absent.

## Guardrails

- Do not invent compensation, benefits, legal terms, or signatory authority.
- Do not sign, send, withdraw, or revise an offer without authority.
- Human approval is required for compensation, offer issuance, and external delivery.

## Example

Validate an approved AI product manager package, render the offer template, flag a mismatched start date, and return a draft with signature and send statuses still pending.

## Common Mistakes

- Treating a draft as a legally issued offer
- Mixing monthly and annual compensation or currencies
- Omitting approval evidence and version history
- Starting onboarding before signed acceptance
