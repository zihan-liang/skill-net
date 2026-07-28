# Business Skills Design

## Goal

Create nine independent, composable Codex skills for the exact customer, opportunity, and project-cooperation workflow supplied by the project team. Eight skills cover the sequence from customer lead through acceptance and renewal; one provides an auditable customer database for customer profiles, contacts, requirements, communications, quotations, contracts, project progress, payments, and renewals.

## Architecture

Use one skill package for each item in the supplied workflow so Codex loads only the instructions and resources needed for the current task. Preserve the supplied list, order, and scope without splitting, merging, adding, or removing skills.

The primary flow is:

`business-customer-lead` → `business-requirement-communication` → `business-opportunity-assessment` → `business-solution-quotation` → `business-negotiation` → `business-contract-signing` → `business-project-delivery-tracking` → `business-acceptance-renewal`

`business-customer-database` supports every stage and records each confirmed mutation in an append-only audit log.

## Packages

1. `business-customer-lead`
   - Capture source, customer identity, contact route, fit hypothesis, consent or lawful-contact basis, owner, next action, and evidence without treating an unverified lead as a customer.
   - Use `assets/customer_lead_template.md` to produce a traceable, minimum-necessary lead record.
2. `business-requirement-communication`
   - Prepare and document discovery conversations covering business goals, stakeholders, users, scope, constraints, budget and timeline signals, decision process, success measures, risks, and agreed next steps.
   - Use `assets/requirement_communication_template.md`; distinguish customer statements, internal interpretations, assumptions, and confirmed requirements.
3. `business-opportunity-assessment`
   - Use `scripts/evaluate_opportunity.py` to evaluate strategic fit, need clarity, authority access, budget readiness, timeline readiness, and delivery fit using evidence-backed scores.
   - Surface critical risks and missing evidence; reserve qualification, priority, pursuit, and disqualification decisions for authorized humans.
4. `business-solution-quotation`
   - Use `assets/solution_quotation_template.md` and `scripts/calculate_quotation.py` to create a versioned solution and draft quotation linked to confirmed requirements.
   - Calculate Decimal-safe line totals, discounts, tax, and total while keeping pricing exceptions, approval, and external sending under human control.
5. `business-negotiation`
   - Use `assets/negotiation_record_template.md` to prepare objectives and limits, track customer and company positions, concessions, dependencies, unresolved points, owners, and next steps.
   - Never invent authority or make binding price, scope, liability, exclusivity, data, service-level, or delivery commitments.
6. `business-contract-signing`
   - Use `assets/contract_signing_checklist.md` and `scripts/validate_contract_signing.py` to validate contract version identity, counterparties, authority, approvals, resolved deviations, required terms, and signature readiness.
   - Return readiness for human signature only; never sign, transmit, or represent a contract as executed without evidence.
7. `business-project-delivery-tracking`
   - Use `assets/project_delivery_tracker.md` and `scripts/evaluate_delivery_progress.py` to track owned milestones, weighted completion, due dates, evidence, blockers, dependencies, changes, risks, and customer decisions.
   - Report schedule and evidence gaps without inventing delivery progress or changing scope.
8. `business-acceptance-renewal`
   - Use `assets/acceptance_renewal_template.md` to compare deliverables with contract acceptance criteria, document exceptions and sign-off evidence, assess renewal value and risks, and prepare an authorized follow-up plan.
   - Keep acceptance, invoice or collection actions, commercial offers, renewal terms, and renewal decisions under named human authority.
9. `business-customer-database`
   - Use `scripts/customer_db.py` and `references/customer_schema.md` for controlled SQLite operations.
   - Store customers, contacts, requirements, communication records, quotations, contracts, project progress, payment records, renewal records, and append-only audit events.

## Common Skill Contract

Each package contains a concise `SKILL.md` with only `name` and a trigger-oriented `description` in YAML frontmatter. The body contains Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes, plus an English workflow and a `**中文摘要：**` line. Each package also contains `agents/openai.yaml` whose default prompt explicitly invokes the corresponding `$skill-name`.

## Data Flow and Statuses

- Stable identifiers link `lead_id`, `customer_id`, `contact_id`, `requirement_id`, `communication_id`, `opportunity_id`, `solution_id`, `quotation_id`, `negotiation_id`, `contract_id`, `project_id`, `milestone_id`, `acceptance_id`, `payment_id`, and `renewal_id`.
- Every downstream step preserves upstream IDs, source references, version, owner, evidence, and decision status.
- Standard statuses distinguish `draft`, `new`, `pending_review`, `qualified`, `not_qualified`, `approved`, `rejected`, `sent`, `negotiating`, `pending_signature`, `signed`, `active`, `in_progress`, `blocked`, `delivered`, `accepted`, `accepted_with_exception`, `due`, `received`, `renewed`, `not_renewed`, and `closed`.
- Every monetary value includes currency. Cross-currency summaries are blocked unless an approved exchange-rate reference and effective date are supplied.
- Corrections create a new version or linked superseding record; audit entries remain append-only.

## Deterministic Tool Contracts

### Opportunity Evaluation

`evaluate_opportunity(data: dict) -> dict` requires stable customer/opportunity IDs and evaluates six dimensions: strategic fit, need clarity, authority access, budget readiness, timeline readiness, and delivery fit. Each 0–5 score requires an evidence reference. Default weights sum to 1; custom non-negative weights must cover all dimensions and sum to 1. Missing evidence reduces coverage, while critical unresolved risks block automated readiness. The result includes a transparent weighted score and `decision_status: human_review_required` when no blocking finding exists.

### Quotation Calculation

`calculate_quotation(data: dict) -> dict` requires quotation, customer, opportunity, solution, and currency identifiers plus non-empty line items. It validates unique line IDs, positive quantities, non-negative prices, discount and tax ranges, quote validity, and required evidence. It calculates line amounts, subtotal, discount, taxable amount, tax, and total using `Decimal` and returns `quotation_status: draft_human_review_required`. It never sends or accepts a quotation.

### Contract Signing Readiness

`validate_contract_signing(data: dict) -> dict` validates contract, customer, opportunity, and quotation identifiers; contract version and SHA-256 document digest; legal counterparties; authorized signatories; approval requirements and evidence; resolved negotiation deviations; required commercial, delivery, acceptance, payment, confidentiality, data/security, intellectual-property, liability, change, termination, and dispute terms. It returns `signature_status: ready_for_human_signature` only when automated checks pass and always returns `external_action: not_performed`.

### Delivery Progress Evaluation

`evaluate_delivery_progress(data: dict) -> dict` requires contract/project IDs and milestones whose non-negative weights total 100. It validates unique milestone IDs, owner, due date, status, evidence for completed or accepted milestones, and progress values consistent with status. It computes weighted completion, reports overdue or blocked work and missing evidence, and returns `delivery_status` without accepting a deliverable or notifying a customer.

### Customer Database

`customer_db.py` exposes `connect_database`, `initialize_database`, `upsert_record`, and `query_record`. Supported entity types are customer, contact, requirement, communication, quotation, contract, project progress, payment, and renewal. Mutations use explicit field allowlists, parameterized SQL, transactions, foreign keys, stable IDs, and audit records containing actor, business purpose, evidence reference, before/after JSON, action, and UTC timestamp.

## Database Boundaries

The SQLite database is a local demonstration, not a production CRM, messaging system, e-signature service, project-management platform, invoicing system, or payment processor. It stores minimum-necessary structured records and restricted references, not identity documents, bank credentials, payment-card data, authentication secrets, full message bodies, call recordings, full proposals or contracts, binary attachments, or unrelated personal data.

Contact data requires a documented business purpose and applicable consent or lawful-contact basis. Query responses return only requested allowlisted fields. Database writes require explicit human confirmation, an authorized actor, a business purpose, and an evidence reference.

## Safety and Control Boundaries

- Require authorized human decisions for lead outreach, requirement confirmation, opportunity qualification or disqualification, pricing and discount exceptions, quotation release, negotiation concessions, contract approval and signature, scope changes, delivery claims, acceptance, collection actions, renewal offers, and database mutations.
- Do not invent customers, contacts, consent, needs, conversations, budgets, authority, scores, quotations, commitments, approvals, signatures, milestones, acceptance evidence, payments, or renewals.
- Do not contact a lead or customer, send a proposal or quotation, make a commitment, sign or transmit a contract, change project scope, claim delivery, issue an invoice, collect funds, or offer a renewal without explicit authority.
- Surface privacy or consent gaps, conflicts, sanctions or compliance concerns, unsupported assumptions, pricing exceptions, unfavorable terms, delivery blockers, acceptance exceptions, overdue payments, renewal risks, and missing evidence.
- Keep legal, tax, privacy, competition, anti-bribery, sanctions, information-security, accounting, credit, and contract decisions with qualified authorized humans.

## Error Handling

Scripts fail closed on missing identifiers, invalid or evidence-free scores, invalid weights, critical unresolved risks, duplicate quotation or milestone IDs, invalid quantities or money, currency gaps, invalid discounts or taxes, malformed document digests, missing approvals or required terms, inconsistent milestone status/progress, duplicate database identifiers, broken foreign keys, unsupported fields, and invalid statuses. Database mutations are transactional so failed validation leaves no partial record or audit event.

## Testing Strategy

- Add `tests/test_business_skills.py` first and confirm each of the nine package-specific tests fails before implementation.
- Add behavior tests before each deterministic script:
  - `tests/test_evaluate_opportunity.py` covers hand-checked weighting, evidence coverage, missing evidence, invalid scores and weights, critical risks, and human decision status.
  - `tests/test_calculate_quotation.py` covers Decimal-safe totals, duplicate lines, quantities and prices, discount and tax boundaries, validity and evidence, and draft status.
  - `tests/test_validate_contract_signing.py` covers complete readiness, missing approvals, unresolved deviations, malformed digest, missing terms or signatory authority, and external-action safety.
  - `tests/test_evaluate_delivery_progress.py` covers hand-checked completion, weights, duplicate milestones, overdue and blocked findings, status/progress consistency, and completion evidence.
  - `tests/test_customer_db.py` covers schema, audited mutations for every entity, uniqueness, foreign keys, validation, minimum-field queries, confirmation, data minimization, and rollback.
- Run the full unittest suite after every package is green.
- Run the official Codex validator for all nine packages and scan for placeholders and broken resource links.
- Exercise the workflow with fictional data only; do not contact external systems.

## Non-Goals

- Live CRM, email, messaging, e-signature, accounting, payment, project-management, sanctions-screening, or production-system integrations
- Autonomous lead scraping, outreach, qualification, pricing, negotiation, contracting, delivery acceptance, invoicing, collection, renewal, or customer-status publication
- Jurisdiction-specific legal, tax, privacy, competition, anti-bribery, sanctions, accounting, or credit advice
- Storage of secrets, identity documents, bank or card data, recordings, message bodies, full proposals or contracts, or confidential attachments

## Success Criteria

- All nine packages are valid, discoverable Codex skills matching the supplied list and order.
- Workflow relationships, stable IDs, evidence requirements, data minimization, and human decision boundaries are explicit.
- Deterministic scripts produce transparent, reproducible results and reject unsafe or inconsistent inputs.
- The customer database represents every requested record category with audited, transactional mutations.
- Existing HR, finance, procurement, and technology tests pass together with all business tests.
