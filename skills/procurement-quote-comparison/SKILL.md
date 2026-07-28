---
name: procurement-quote-comparison
description: Use when supplier quotations or RFQ responses need completeness checks, normalized commercial comparison, transparent scoring, or an approval-ready comparison table.
---

# Procurement Quote Comparison

## Overview

Compare quotations consistently while preserving exclusions, evidence, assumptions, and human award authority.

**中文摘要：** 对供应商报价进行完整性校验、同币种归一和透明评分；保留所有不合格原因，排名仅供人工选商参考。

## Required Inputs

- Approved requirement, `request_id`, `rfq_id`, mandatory items, and quantities
- Comparison date, currency, scoring weights, and approved exchange-rate evidence if needed
- Supplier quote IDs, line prices, validity, delivery days, and source references
- Quality/service scores with dated evidence and conflict declarations

## Workflow

1. Confirm the RFQ and requirement versions match every quotation.
2. Run `scripts/compare_quotes.py` with requirement and quote JSON files.
3. Review missing items, insufficient quantities, expiry, currency, evidence, and duplicate-ID findings.
4. Keep every submitted quote visible; rank only eligible quotes.
5. Explain price, delivery, quality, service, weights, assumptions, and score rounding.
6. Add commercial terms not captured by the script, including tax, freight, warranty, payment, and lifecycle cost.
7. Route the comparison to conflict-free human reviewers; do not announce an award.

## Output Contract

Return `request_id`, `rfq_id`, comparison date/currency, weights, all quotation rows, totals, eligibility, blocking findings, dimension scores, eligible ranking, evidence references, and `decision_status: human_review_required`.

## SkillNet Relationships

- Follows `procurement-supplier-sourcing`.
- Supplies evidence to `procurement-supplier-selection`.
- Stores quote history through `procurement-supplier-database` after confirmation.

## Guardrails

- Do not invent quotes, terms, exchange rates, scores, evidence, or supplier responses.
- Do not compare currencies without an approved rate and date or hide non-compliant bids.
- Human approval is required for RFQ release, scoring exceptions, negotiation, and supplier award.

## Example

Compare three CNY laptop quotations using 40% price, 25% delivery, 20% quality, and 15% service, retaining one expired quote as ineligible.

## Common Mistakes

- Ranking incomplete or expired quotes
- Comparing headline prices while omitting tax, freight, or required quantities
- Giving quality/service scores without evidence
- Treating the highest calculated score as an automatic award
