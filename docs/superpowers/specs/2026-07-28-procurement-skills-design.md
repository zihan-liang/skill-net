# Procurement Skills Design

## Goal

Create nine independent, composable Codex skills for the exact startup procurement and supplier-management workflow supplied by the project team. Eight skills cover the operating sequence from procurement requirement through supplier evaluation; one provides an auditable supplier database for qualifications, offerings, quotations, contracts, deliveries, and evaluations.

## Architecture

Use one skill package for each item in the supplied workflow so Codex loads only the instructions and resources needed for the current task. Preserve the supplied list, order, and scope without splitting, merging, adding, or removing skills.

The primary flow is:

`procurement-requirement` → `procurement-budget-confirmation` → `procurement-supplier-sourcing` → `procurement-quote-comparison` → `procurement-supplier-selection` → `procurement-contract-order` → `procurement-delivery-acceptance` → `procurement-supplier-evaluation`

`procurement-supplier-database` supports every stage and records each confirmed mutation in an append-only audit log.

## Packages

1. `procurement-requirement`
   - Capture the requester, department, business purpose, category, quantity, target date, estimated value, supporting evidence, and measurable functional, technical, service-level, delivery, quality, sustainability, and acceptance criteria.
   - Use `assets/procurement_request_template.md` to produce one traceable requirement and distinguish mandatory criteria from preferences.
2. `procurement-budget-confirmation`
   - Confirm the approved budget line, remaining amount, currency, spending threshold, approval route, and segregation of duties.
   - Use `assets/budget_confirmation_template.md`; never infer budget availability or approval.
3. `procurement-supplier-sourcing`
   - Build a traceable candidate list and assess qualifications, capacity, conflicts, compliance evidence, and product/service fit.
   - Treat unsupported or expired evidence as a gap, not as a pass.
4. `procurement-quote-comparison`
   - Use `scripts/compare_quotes.py` to check quote completeness, normalize line totals, and calculate transparent price, delivery, quality, and service scores.
   - Keep non-compliant bids in the comparison with blocking reasons rather than silently dropping them.
5. `procurement-supplier-selection`
   - Use `assets/supplier_selection_memo.md` to turn evidence and comparison results into a reviewable recommendation.
   - Reserve the award decision for an authorized, conflict-free human approver.
6. `procurement-contract-order`
   - Use `scripts/render_purchase_order.py` and `assets/purchase_order_template.md` to render a draft purchase order from an approved selection.
   - Require distinct selection and order approvals; never sign, send, or place a real order.
7. `procurement-delivery-acceptance`
   - Use `assets/delivery_acceptance_template.md` to compare delivered quantity, condition, quality, documents, and dates with the approved order and acceptance criteria.
   - Record discrepancies, quarantine/return recommendations, and the human acceptance decision separately.
8. `procurement-supplier-evaluation`
   - Use `scripts/evaluate_supplier.py` to calculate an evidence-backed weighted score for delivery, quality, service, commercial performance, and compliance.
   - Report evidence coverage and never auto-blacklist or renew a supplier.
9. `procurement-supplier-database`
    - Use `scripts/supplier_db.py` and `references/supplier_schema.md` for controlled SQLite operations.
    - Store suppliers, qualifications, offerings, quotation history, contracts, deliveries, evaluations, and append-only audit events.

## Common Skill Contract

Each package contains a concise `SKILL.md` with only `name` and a trigger-oriented `description` in YAML frontmatter. The body contains Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes, plus an English workflow and a `**中文摘要：**` line. Each package also contains `agents/openai.yaml` whose default prompt explicitly invokes the corresponding `$skill-name`.

## Data Flow and Statuses

- Stable identifiers link `request_id`, `requirement_id`, `budget_check_id`, `supplier_id`, `rfq_id`, `quote_id`, `selection_id`, `contract_id`, `order_id`, `delivery_id`, and `evaluation_id`.
- Every downstream step preserves upstream IDs, source references, version, and decision status.
- Standard statuses distinguish `draft`, `pending_review`, `approved`, `rejected`, `issued`, `delivered`, `accepted`, `accepted_with_exception`, and `closed`.
- Every monetary value includes currency. Cross-currency comparison is blocked unless an approved exchange-rate reference and comparison date are supplied.
- Corrections create a new version or status event; audit entries remain append-only.

## Deterministic Tool Contracts

### Quote Comparison

`compare_quotes(requirement: dict, quotes: list[dict]) -> dict` validates identifiers, required items, positive quantities and prices, currency, quote validity, and score ranges. It returns eligibility findings, Decimal-safe totals, dimension scores, weighted scores, ranking among eligible quotes, evidence references, and `decision_status: human_review_required`.

Default weights are price 40%, delivery 25%, quality 20%, and service 15%; supplied weights must be non-negative and sum to 1. Missing mandatory items, currency mismatch, expired quotes, or missing evidence makes a quote ineligible.

### Purchase Order Rendering

`render_purchase_order(template: str, data: dict) -> str` requires approved supplier selection and approved order release evidence. It validates required placeholders and values, then renders a draft marked `NOT ISSUED`. It does not send, sign, or create an external order.

### Supplier Evaluation

`evaluate_supplier(data: dict) -> dict` uses delivery 25%, quality 30%, service 20%, commercial performance 15%, and compliance 10%. Each 0–5 score requires an evidence reference. Missing dimensions reduce evidence coverage and are excluded from the weighted denominator; the result remains human review required.

### Supplier Database

`supplier_db.py` exposes `connect_database`, `initialize_database`, `upsert_record`, and `query_record`. Supported entity types are supplier, qualification, offering, quote, contract, delivery, and evaluation. Mutations use explicit field allowlists, parameterized SQL, transactions, foreign keys, stable IDs, and audit records containing actor, business purpose, evidence reference, before/after JSON, action, and UTC timestamp.

## Database Boundaries

The SQLite database is a local demonstration, not an ERP, vendor portal, e-signature service, or payment system. It stores only supplier-management fields required for this workflow. Raw bank credentials, identity documents, authentication secrets, private keys, full contracts, and confidential attachments are represented by restricted references rather than stored in general-purpose tables.

Query responses return only requested allowlisted fields. Database writes require explicit human confirmation, an authorized actor, a business purpose, and evidence reference.

## Safety and Control Boundaries

- Require authorized human decisions for budget confirmation, sourcing outreach, RFQ release, supplier award, contract acceptance, purchase-order release, delivery acceptance, supplier rating publication, and database mutations.
- Enforce segregation of duties: a requester cannot be the sole budget approver, selector, and order releaser for the same purchase.
- Do not invent requirements, budget, suppliers, quotes, qualifications, conflicts, approvals, contract terms, delivery evidence, or ratings.
- Do not contact suppliers, publish an RFQ, sign a contract, issue an order, accept goods, reject a delivery, blacklist a supplier, or write to a live procurement system without explicit authority.
- Surface conflicts of interest, sanctions/compliance gaps, expired credentials, single-source exceptions, quote mismatches, delivery defects, and missing evidence as review findings.
- Keep legal, regulatory, tax, trade-control, information-security, and contract decisions with qualified authorized humans.

## Error Handling

Scripts fail closed on missing identifiers, invalid or non-positive quantities and money, currency mismatches, invalid weights or scores, duplicate stable identifiers, broken foreign keys, missing approval evidence, and unsupported fields. Database mutations are transactional so failed validation leaves no partial record or audit event.

## Testing Strategy

- Add `tests/test_procurement_skills.py` first and confirm each of the nine package-specific tests fails before implementation.
- Add behavior tests before each deterministic script:
  - `tests/test_compare_quotes.py` covers totals, ranking, non-compliance, expiry, currency, weights, and duplicate IDs.
  - `tests/test_render_purchase_order.py` covers approvals, required values, unresolved placeholders, and successful rendering.
  - `tests/test_evaluate_supplier.py` covers weighted scoring, evidence coverage, missing evidence, invalid scores, and weights.
  - `tests/test_supplier_db.py` covers schema, audited mutations, uniqueness, validation, minimum-field queries, and rollback.
- Run the full unittest suite after every package is green.
- Run the official Codex validator for all nine packages and scan for placeholders and broken resource links.
- Exercise the workflow with fictional data only; do not contact external systems.

## Non-Goals

- Live ERP, banking, supplier portal, e-signature, logistics, sanctions-screening, or accounting integrations
- Autonomous vendor outreach, negotiation, award, contracting, ordering, acceptance, payment, suspension, or blacklisting
- Jurisdiction-specific legal, tax, trade, product-safety, or regulatory advice
- Inventory planning, accounts payable execution, expense reimbursement, or manufacturing production control

## Success Criteria

- All nine packages are valid, discoverable Codex skills with explicit workflow relationships and human decision boundaries.
- Deterministic scripts produce transparent, reproducible results and reject unsafe or inconsistent inputs.
- The supplier database represents every requested record category with audited, transactional mutations.
- Existing HR and finance tests pass together with all procurement tests.
