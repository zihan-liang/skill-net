# Business Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the nine business Codex skills in the exact order and scope supplied by the project team.

**Architecture:** Keep each workflow item in an independent `skills/business-*` package with concise instructions and generated UI metadata. Use Markdown assets for human-reviewed records and Python standard-library scripts for opportunity scoring, quotation arithmetic, signature-readiness checks, delivery-progress evaluation, and transactional SQLite storage.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, SQLite, Codex `skill-creator` initialization and validation scripts.

## Global Constraints

- Preserve exactly these nine skills and this order: customer lead, requirement communication, opportunity assessment, solution and quotation, business negotiation, contract signing, project delivery tracking, acceptance and renewal, customer database.
- Keep every `SKILL.md` below 500 words with only `name` and trigger-oriented `description` frontmatter.
- Include Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes.
- Include an English workflow and a `**中文摘要：**` line in every skill.
- Require authorized human decisions for outreach, requirement confirmation, qualification, pricing, quotation release, negotiation concessions, contract signature, scope changes, delivery claims, acceptance, collection, renewal, and database mutation.
- Never invent customer, consent, conversation, commercial, approval, signature, delivery, payment, or renewal evidence; never modify or contact a live external system in demonstrations.
- Store only minimum-necessary structured data and restricted references in the customer database, never secrets, identity documents, bank/card data, recordings, message bodies, or full proposals/contracts.
- Record database mutations with actor, business purpose, evidence reference, before/after values, confirmation, and UTC timestamp.
- Create every package through `skill-creator/scripts/init_skill.py` and validate it with `quick_validate.py`.

---

### Task 1: Customer Lead Skill

**Files:**
- Create: `tests/test_business_skills.py`
- Create: `skills/business-customer-lead/SKILL.md`
- Create: `skills/business-customer-lead/agents/openai.yaml`
- Create: `skills/business-customer-lead/assets/customer_lead_template.md`

**Interfaces:**
- Consumes: lead source, organization, fit hypothesis, business contact route, consent or lawful-contact basis, owner, evidence, and next action.
- Produces: `lead_id`, source, customer hypothesis, contact basis, evidence gaps, owner, next action, and `status: new` or `pending_review`.

- [ ] Write a failing structural contract whose `test_customer_lead` calls `validate_skill("business-customer-lead")`; validate metadata, headings, Chinese summary, human boundary, resources, word count, placeholder absence, and `$business-customer-lead` UI prompt.
- [ ] Run `python3 -m unittest tests.test_business_skills.BusinessSkillContractTests.test_customer_lead` and confirm failure because the package is absent.
- [ ] Initialize with `assets`, replace generated content, and create the minimum-necessary lead template.
- [ ] Run the targeted test, official validator, and existing green tests; commit with `feat: add business customer lead skill`.

### Task 2: Requirement Communication Skill

**Files:**
- Create: `skills/business-requirement-communication/SKILL.md`
- Create: `skills/business-requirement-communication/agents/openai.yaml`
- Create: `skills/business-requirement-communication/assets/requirement_communication_template.md`

**Interfaces:**
- Consumes: customer/contact/lead IDs, discovery objectives, stakeholders, customer statements, constraints, budget/timeline signals, decision process, consent, and evidence.
- Produces: `requirement_id`, `communication_id`, confirmed needs, assumptions, open questions, success measures, owners, next steps, and review status.

- [ ] Run the already-written `test_requirement_communication` and confirm its absent-package failure.
- [ ] Initialize with `assets`, implement the discovery and confirmation workflow, and create the communication template.
- [ ] Run targeted/full tests and official validation; commit with `feat: add business requirement communication skill`.

### Task 3: Opportunity Assessment Skill and Evaluator

**Files:**
- Create: `tests/test_evaluate_opportunity.py`
- Create: `skills/business-opportunity-assessment/SKILL.md`
- Create: `skills/business-opportunity-assessment/agents/openai.yaml`
- Create: `skills/business-opportunity-assessment/scripts/evaluate_opportunity.py`

**Interfaces:**
- Produces: `evaluate_opportunity(data: dict) -> dict`.
- Returns: customer/opportunity IDs, weighted score, evidence coverage, dimension results, risks, blocking findings, automated readiness, and human decision status.

- [ ] Write literal behavior tests for the six default weights, custom weights, evidence coverage, missing evidence, out-of-range scores, critical unresolved risks, and human review; confirm import failure.
- [ ] Run structural `test_opportunity_assessment` and confirm the absent-package failure.
- [ ] Initialize with `scripts`; implement Decimal-safe scoring and a JSON CLI using no external dependency.
- [ ] Run behavior/structural/full tests and official validation; commit with `feat: add business opportunity assessment skill`.

### Task 4: Solution and Quotation Skill

**Files:**
- Create: `tests/test_calculate_quotation.py`
- Create: `skills/business-solution-quotation/SKILL.md`
- Create: `skills/business-solution-quotation/agents/openai.yaml`
- Create: `skills/business-solution-quotation/assets/solution_quotation_template.md`
- Create: `skills/business-solution-quotation/scripts/calculate_quotation.py`

**Interfaces:**
- Produces: `calculate_quotation(data: dict) -> dict`.
- Returns: linked IDs, normalized lines, subtotal, discount, taxable amount, tax, total, currency, evidence, findings, and `quotation_status: draft_human_review_required`.

- [ ] Write hand-calculated tests for line totals, discount, tax, Decimal rounding, duplicate line IDs, invalid quantity/price/rates, missing evidence or validity, and draft-only status; confirm import failure.
- [ ] Run structural `test_solution_quotation` and confirm the absent-package failure.
- [ ] Initialize with `scripts,assets`; implement the calculator, JSON CLI, and solution/quotation template.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add business solution quotation skill`.

### Task 5: Business Negotiation Skill

**Files:**
- Create: `skills/business-negotiation/SKILL.md`
- Create: `skills/business-negotiation/agents/openai.yaml`
- Create: `skills/business-negotiation/assets/negotiation_record_template.md`

**Interfaces:**
- Consumes: approved negotiation mandate, customer/opportunity/quotation IDs, objectives, limits, positions, authority, deviations, risks, and evidence.
- Produces: `negotiation_id`, agenda, position matrix, concessions log, unresolved points, approval requests, owners, next steps, and `status: human_review_required`.

- [ ] Run `test_negotiation` and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement preparation/record/escalation instructions, and create the negotiation record template.
- [ ] Run targeted/full tests and validation; commit with `feat: add business negotiation skill`.

### Task 6: Contract Signing Skill and Readiness Validator

**Files:**
- Create: `tests/test_validate_contract_signing.py`
- Create: `skills/business-contract-signing/SKILL.md`
- Create: `skills/business-contract-signing/agents/openai.yaml`
- Create: `skills/business-contract-signing/assets/contract_signing_checklist.md`
- Create: `skills/business-contract-signing/scripts/validate_contract_signing.py`

**Interfaces:**
- Produces: `validate_contract_signing(data: dict) -> dict`.
- Returns: contract/version/digest and linked IDs, counterparties, approval and term findings, automated readiness, `signature_status`, and `external_action: not_performed`.

- [ ] Write tests for a complete contract packet, missing approval, unresolved deviation, malformed SHA-256 digest, missing required term, absent signatory authority, and no external action; confirm import failure.
- [ ] Run structural `test_contract_signing` and confirm the absent-package failure.
- [ ] Initialize with `scripts,assets`; implement fail-closed readiness validation, JSON CLI, and checklist.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add business contract signing skill`.

### Task 7: Project Delivery Tracking Skill and Evaluator

**Files:**
- Create: `tests/test_evaluate_delivery_progress.py`
- Create: `skills/business-project-delivery-tracking/SKILL.md`
- Create: `skills/business-project-delivery-tracking/agents/openai.yaml`
- Create: `skills/business-project-delivery-tracking/assets/project_delivery_tracker.md`
- Create: `skills/business-project-delivery-tracking/scripts/evaluate_delivery_progress.py`

**Interfaces:**
- Produces: `evaluate_delivery_progress(data: dict) -> dict`.
- Returns: contract/project IDs, milestone count, weighted completion, overdue/blocked/missing-evidence findings, automated health, and delivery status.

- [ ] Write hand-checked tests for weighted completion, weights totaling 100, duplicate milestone IDs, overdue and blocked milestones, status/progress mismatch, and missing completion evidence; confirm import failure.
- [ ] Run structural `test_project_delivery_tracking` and confirm the absent-package failure.
- [ ] Initialize with `scripts,assets`; implement deterministic evaluation, JSON CLI, and tracking template.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add business project delivery tracking skill`.

### Task 8: Acceptance and Renewal Skill

**Files:**
- Create: `skills/business-acceptance-renewal/SKILL.md`
- Create: `skills/business-acceptance-renewal/agents/openai.yaml`
- Create: `skills/business-acceptance-renewal/assets/acceptance_renewal_template.md`

**Interfaces:**
- Consumes: contract/project/deliverable IDs, acceptance criteria, delivery and customer evidence, exceptions, payment status, outcomes, renewal date, value/risk evidence, and authority.
- Produces: `acceptance_id`, criteria matrix, exceptions, sign-off route/evidence, payment follow-up, renewal assessment, proposed next step, owners, and human decision statuses.

- [ ] Run `test_acceptance_renewal` and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement acceptance/exception/value/renewal workflows, and create the combined template.
- [ ] Run targeted/full tests and validation; commit with `feat: add business acceptance renewal skill`.

### Task 9: Customer Database Skill and SQLite Tool

**Files:**
- Create: `tests/test_customer_db.py`
- Create: `skills/business-customer-database/SKILL.md`
- Create: `skills/business-customer-database/agents/openai.yaml`
- Create: `skills/business-customer-database/scripts/customer_db.py`
- Create: `skills/business-customer-database/references/customer_schema.md`

**Interfaces:**
- Produces: `connect_database`, `initialize_database`, `upsert_record`, and `query_record`.
- Supported entities: customer, contact, requirement, communication, quotation, contract, project progress, payment, and renewal; every mutation returns the stored record and `audit_event_id`.

- [ ] Write tests for all tables, one mutation per entity, human confirmation, unique contacts/quotations/contracts, foreign-key relationships, money/currency and status validation, sensitive-field rejection, minimum queries, before/after audits, and rollback; confirm import failure.
- [ ] Run structural `test_customer_database` and confirm the absent-package failure.
- [ ] Initialize with `scripts,references`; implement allowlisted parameterized SQLite operations, append-only audit triggers, and schema documentation.
- [ ] Run database/structural/full tests and validation; commit with `feat: add business customer database skill`.

### Task 10: Collection Verification and Demonstration

**Files:**
- Modify: `.gitignore` only if disposable database or cache artifacts are not already excluded.

**Interfaces:**
- Consumes: all nine packages and tests.
- Produces: a validated business skill collection and fictional local demonstration output.

- [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'` and require zero failures.
- [ ] Run `quick_validate.py` on every `skills/business-*` directory.
- [ ] Run `git diff --check`, compile scripts, execute each script's `--help`, scan for incomplete placeholders, validate resource references, and check every skill is below 500 words.
- [ ] With fictional data, evaluate an opportunity, calculate a quotation, validate a contract-signing packet, evaluate project delivery, initialize a disposable database, write every record category, query minimum fields, and inspect audit events; perform no external mutation.
- [ ] Review the diff for exact nine-skill scope and safety, then commit any final business-only corrections.
