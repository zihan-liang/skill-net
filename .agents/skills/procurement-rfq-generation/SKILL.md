---
name: procurement-rfq-generation
description: Use when an approved procurement requirement and admitted supplier list need an RFQ draft, inquiry scope, quotation template, deadline, and recipient list; not for sending or comparing quotes.
---

# Procurement RFQ Generation

## Overview

Create one versioned, supplier-consistent request for quotation without releasing it externally.

**中文摘要：** 根据采购需求和技术规格生成 RFQ、询价范围、报价模板、截止日期与供应商发送清单；不负责发送或比价。

## Required Inputs

- Approved requirement/version, technical specification, budget-check reference, and owner
- Human-admitted suppliers and qualification references
- Items/services, quantities, commercial assumptions, response fields, deadline/timezone, and communication authority

## Workflow

1. Read `assets/rfq_template.md`; assign `rfq_id` and version.
2. Freeze the requirement and technical-specification references used for this RFQ.
3. Define identical scope, quantities, mandatory response fields, pricing basis, tax/freight treatment, delivery, warranty, service, validity, and evidence requirements.
4. Create a normalized quotation template and clarification channel.
5. Set deadline, timezone, submission method, confidentiality, amendment, and late-response rules.
6. Build the recipient list only from admitted suppliers and record exceptions.
7. Run a completeness/equality review and route the draft for release approval.

## Output Contract

Return RFQ/request/spec IDs and versions, inquiry scope, quotation template, commercial assumptions, response/evidence requirements, deadline/timezone, recipient list, exceptions, approval route, and `send_status: not_sent`.

## SkillNet Relationships

- Follows `procurement-supplier-qualification`.
- Precedes `procurement-quote-comparison` after authorized release and responses.
- Uses technical parameters confirmed by `technology-specification-confirmation` when applicable.

## Approval Controls

- Do not invent specifications, suppliers, deadlines, terms, release approval, or responses.
- Preserve an immutable RFQ version and an audit reference for every approved amendment.
- Human approval is required for recipients, exceptions, RFQ release, amendment, deadline change, and external communication.

## Exception Handling

- Stop release when supplier versions differ, required specifications or pricing fields are missing, the deadline is ambiguous, or an unqualified supplier appears.
- Issue a versioned amendment through the authorized route; never silently edit a released RFQ.

## Handoff

After authorized release and response collection, pass the exact RFQ version, response population, amendments, timestamps, and source references to `procurement-quote-comparison`.

## Example

Draft an RFQ for 20 laptops with one pricing table, delivery/warranty fields, a Shanghai-time deadline, and three admitted recipients.

## Common Mistakes

- Sending different scope to different suppliers
- Omitting tax, freight, currency, validity, or timezone
- Treating a draft as released
