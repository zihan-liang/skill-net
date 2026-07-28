---
name: procurement-quote-comparison
description: Use when RFQ responses need completeness checks, line normalization, currency and commercial-term comparison, or a comparison table; not for qualification, composite supplier scoring, or selection.
---

# Procurement Quote Comparison

## Overview

Normalize quotations against one RFQ and compare commercial facts. Do not blend qualification, quality, or risk judgments into this stage.

**中文摘要：** 只负责报价完整性、行项目、币种、税费、运费、折扣、付款与交付条款的标准化商业比较，不负责供应商综合评分或选商。

## Required Inputs

- Approved requirement and released RFQ IDs/versions, items, quantities, currency, and comparison date
- Every received quote with source reference, validity, line prices, discount, tax, freight, delivery, payment, and warranty terms
- Authorized exchange-rate evidence if currencies must be normalized

## Workflow

1. Confirm every quote answers the same RFQ version and preserve late/incomplete responses.
2. Encode the requirement and quotes as JSON and run `scripts/compare_quotes.py`.
3. Review missing items, quantities, source references, expiry, and currency findings.
4. Normalize line subtotal, discount, tax, freight, total price, payment, warranty, and delivery terms.
5. Apply only approved dated exchange rates; otherwise keep currencies separate and block comparison.
6. Keep all responses visible and explain commercial assumptions or exclusions.
7. Route the commercial table for review without scoring or awarding a supplier.

## Output Contract

Return request/RFQ IDs, comparison date/currency, all quote rows, normalized line and total amounts, commercial terms, eligibility findings, commercial ordering, evidence references, and `decision_status: human_review_required`.

## SkillNet Relationships

- Follows `procurement-rfq-generation` and precedes `procurement-supplier-scoring`.
- Supplies normalized price and commercial evidence; it does not decide dimension weights.
- Keeps qualification evidence in `procurement-supplier-qualification`.

## Approval Controls

- Do not invent quotes, terms, responses, exchange rates, or evidence; preserve every submitted response and version.
- Use stable IDs, minimum fields, and restricted references rather than storing full confidential attachments in open records.
- Human approval is required for normalization exceptions, exchange rates, late bids, negotiation, and any external communication.

## Exception Handling

- Mark a quote ineligible when mandatory items, quantities, source evidence, currency basis, or validity fail; do not delete it.
- Escalate ambiguous taxes, bundled pricing, conditional discounts, or inconsistent RFQ versions for clarification.

## Handoff

Pass the immutable commercial comparison, all quote rows, findings, assumptions, and evidence references to `procurement-supplier-scoring`; do not label the cheapest supplier selected.

## Example

Normalize three laptop quotes into CNY line totals, tax, freight, discount, payment, delivery, and warranty columns while retaining one expired response.

## Common Mistakes

- Adding qualification or quality scores to the comparison
- Comparing headline price without tax, freight, or required quantities
- Treating commercial ordering as supplier selection
