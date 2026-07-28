---
name: business-customer-lead
description: Use when a potential customer, merchant, partner organization, referral, inbound inquiry, or target account needs a traceable lead record before outreach or opportunity qualification.
---

# Business Customer Lead

## Overview

Capture a minimum-necessary, evidence-based customer lead without treating an unverified prospect as a confirmed customer or authorizing outreach.

**中文摘要：** 记录客户线索来源、潜在需求、联系依据、负责人和下一步；未经授权不得抓取个人信息、联系客户或把假设写成事实。

## Required Inputs

- Lead source, source date/reference, organization or customer hypothesis, market segment, and location
- Minimum business contact route, consent or lawful-contact basis, suppression status, and data source
- Fit hypothesis, potential need, relationship context, owner, priority rationale, and next action
- Privacy, conflict, sanctions/compliance, channel, and retention requirements

## Workflow

1. Read `assets/customer_lead_template.md`; assign a stable `lead_id` and record provenance.
2. Separate verified facts, source claims, internal hypotheses, and unknowns.
3. Minimize contact data; record the business purpose and applicable consent or lawful-contact basis.
4. Check duplicates, suppression or opt-out status, conflicts, restricted-party concerns, and source reliability.
5. Describe the fit hypothesis and potential need without inventing budget, authority, timing, or interest.
6. Define an owner, authorized channel, proposed next action, due date, and evidence needed for qualification.
7. Route outreach, rejection, conversion, and retention decisions to authorized humans.

## Output Contract

Return `lead_id`, source/evidence, minimum customer/contact data, verified facts, hypotheses, gaps, contact basis, compliance findings, owner, next action, and `lead_status`.

## SkillNet Relationships

- Precedes `business-requirement-communication`.
- Supplies confirmed identifiers and provenance to `business-customer-database`.
- May receive target-market criteria from strategy, product, or marketing skills.

## Guardrails

- Do not scrape, enrich, buy, expose, or retain personal data without authority and a valid purpose.
- Do not invent consent, customer interest, need, budget, decision authority, or relationship history.
- Human approval is required before outreach, suppression override, qualification, rejection, conversion, export, or database mutation.

## Example

Record a referred Shanghai restaurant group as `LEAD-14`, cite the referral, mark interest as unverified, record an authorized business contact route, and propose a discovery call for human approval.

## Common Mistakes

- Treating a target account as an interested customer
- Copying unnecessary personal information into the lead
- Omitting source, consent/contact basis, owner, or opt-out check
- Contacting the lead while only preparing a record
