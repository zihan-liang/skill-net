# Procurement Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the nine procurement Codex skills in the exact order and scope supplied by the project team.

**Architecture:** Keep each workflow item in an independent `skills/procurement-*` package with concise instructions and generated UI metadata. Use Markdown assets for human-reviewed records and Python standard-library scripts for quotation comparison, purchase-order rendering, supplier evaluation, and transactional SQLite storage.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, SQLite, Codex `skill-creator` initialization and validation scripts.

## Global Constraints

- Preserve exactly these nine skills and this order: procurement requirement, budget confirmation, supplier sourcing, quote comparison, supplier selection, contract/order generation, delivery acceptance, supplier evaluation, supplier database.
- Keep every `SKILL.md` below 500 words with only `name` and trigger-oriented `description` frontmatter.
- Include Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes.
- Include an English workflow and a `**中文摘要：**` line in every skill.
- Require authorized human decisions for budget confirmation, outreach, RFQ release, supplier award, contracting, order release, delivery acceptance, rating publication, and database mutations.
- Never contact suppliers, sign or send contracts, issue live orders, accept/reject goods, blacklist suppliers, or write to external procurement systems.
- Use `Decimal` for monetary arithmetic and explicit currencies for every monetary record.
- Record database mutations with actor, business purpose, evidence reference, before/after values, and UTC timestamp.
- Create every package through `skill-creator/scripts/init_skill.py` and validate it with `quick_validate.py`.

---

### Task 1: Procurement Requirement Skill

**Files:**
- Create: `tests/test_procurement_skills.py`
- Create: `skills/procurement-requirement/SKILL.md`
- Create: `skills/procurement-requirement/agents/openai.yaml`
- Create: `skills/procurement-requirement/assets/procurement_request_template.md`

**Interfaces:**
- Consumes: requester, department, business purpose, category, quantity, target date, estimated value/currency, supporting evidence, measurable specifications, acceptance criteria.
- Produces: `request_id`, requirement version, mandatory/preferred criteria, missing information, source references, `status: draft`.

- [ ] **Step 1: Write the failing structural contract**

Create a `unittest` contract whose `test_requirement` calls `validate_skill("procurement-requirement")`. Validate frontmatter, required headings, Chinese summary, human boundary, resource references, word count, placeholder absence, and `$procurement-requirement` in UI metadata.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_procurement_skills.ProcurementSkillContractTests.test_requirement`

Expected: FAIL because `skills/procurement-requirement/SKILL.md` is absent.

- [ ] **Step 3: Initialize and implement**

Run `init_skill.py procurement-requirement --path skills --resources assets` with explicit interface values. Replace generated content and create the request template with traceable IDs and measurable criteria.

- [ ] **Step 4: Verify and commit**

Run the targeted test, `quick_validate.py skills/procurement-requirement`, and the full suite. Commit with `feat: add procurement requirement skill`.

### Task 2: Budget Confirmation Skill

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `skills/procurement-budget-confirmation/SKILL.md`
- Create: `skills/procurement-budget-confirmation/agents/openai.yaml`
- Create: `skills/procurement-budget-confirmation/assets/budget_confirmation_template.md`

**Interfaces:**
- Consumes: requirement, approved budget version/line, available amount, currency, threshold policy, approver identities.
- Produces: `budget_check_id`, availability calculation, policy findings, approval route, evidence gaps, `confirmation_status: human_review_required`.

- [ ] Add `test_budget_confirmation`; run it and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement the concise workflow, and create the budget confirmation record.
- [ ] Run targeted/full tests and the official validator; commit with `feat: add procurement budget confirmation skill`.

### Task 3: Supplier Sourcing Skill

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `skills/procurement-supplier-sourcing/SKILL.md`
- Create: `skills/procurement-supplier-sourcing/agents/openai.yaml`

**Interfaces:**
- Consumes: approved requirement, category strategy, supplier records, qualification evidence, conflict declarations, sourcing constraints.
- Produces: sourcing brief, candidate list, qualification/evidence matrix, exclusions with reasons, outreach draft, `outreach_status: not_sent`.

- [ ] Add `test_supplier_sourcing`; run it and confirm the missing-package failure.
- [ ] Initialize without resource folders and implement evidence, conflict, capacity, competition, and qualification checks.
- [ ] Run targeted/full tests and the validator; commit with `feat: add procurement supplier sourcing skill`.

### Task 4: Quote Comparison Skill and Script

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `tests/test_compare_quotes.py`
- Create: `skills/procurement-quote-comparison/SKILL.md`
- Create: `skills/procurement-quote-comparison/agents/openai.yaml`
- Create: `skills/procurement-quote-comparison/scripts/compare_quotes.py`

**Interfaces:**
- Produces: `compare_quotes(requirement: dict, quotes: list[dict]) -> dict`.
- Returns: `rfq_id`, currency, weights, per-quote eligibility, blocking findings, total price, dimension scores, weighted score, rank, evidence references, and `decision_status: human_review_required`.

- [ ] **Step 1: Write behavior tests before the script**

Use literal fixtures to test hand-calculated totals/ranking, missing mandatory items, currency mismatch, expired quotes, invalid/unsummed weights, duplicate quote IDs, and invalid monetary values.

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest tests.test_compare_quotes` and confirm import failure because the script is absent. Add the structural method and confirm its missing-package failure.

- [ ] **Step 3: Implement minimal behavior and package**

Use `Decimal`; keep ineligible quotes with explicit reasons; rank only eligible quotes; require evidence for quality/service scores; expose a JSON CLI. Initialize with `scripts` and document how to run the tool.

- [ ] **Step 4: Verify and commit**

Run behavior/structural/full tests and official validation. Commit with `feat: add procurement quote comparison skill`.

### Task 5: Supplier Selection Skill

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `skills/procurement-supplier-selection/SKILL.md`
- Create: `skills/procurement-supplier-selection/agents/openai.yaml`
- Create: `skills/procurement-supplier-selection/assets/supplier_selection_memo.md`

**Interfaces:**
- Consumes: approved sourcing list, quote comparison, due-diligence evidence, conflicts, single-source justification, approver route.
- Produces: `selection_id`, evidence matrix, risks/exceptions, recommendation, dissent, approval route, `award_status: human_review_required`.

- [ ] Add `test_supplier_selection`; run it and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement the selection workflow, and create the decision memo.
- [ ] Run targeted/full tests and the validator; commit with `feat: add procurement supplier selection skill`.

### Task 6: Contract and Order Skill, Template, and Renderer

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `tests/test_render_purchase_order.py`
- Create: `skills/procurement-contract-order/SKILL.md`
- Create: `skills/procurement-contract-order/agents/openai.yaml`
- Create: `skills/procurement-contract-order/assets/purchase_order_template.md`
- Create: `skills/procurement-contract-order/scripts/render_purchase_order.py`

**Interfaces:**
- Produces: `render_purchase_order(template: str, data: dict) -> str`.
- Requires: approved selection evidence, approved order release evidence, stable IDs, supplier/order lines, currency, delivery/acceptance terms, and source references.

- [ ] Write tests for both approvals, missing values, unresolved placeholders, and a literal successful render; confirm import failure.
- [ ] Add the structural method and confirm the absent-package failure.
- [ ] Initialize with `scripts,assets`; implement exact placeholder replacement and permanent `NOT ISSUED` marking.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add procurement contract and order skill`.

### Task 7: Delivery Acceptance Skill

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `skills/procurement-delivery-acceptance/SKILL.md`
- Create: `skills/procurement-delivery-acceptance/agents/openai.yaml`
- Create: `skills/procurement-delivery-acceptance/assets/delivery_acceptance_template.md`

**Interfaces:**
- Consumes: approved order, delivery record, inspection evidence, quantity/quality checks, acceptance criteria, receiver identity.
- Produces: `delivery_id`, discrepancy log, evidence references, recommended disposition, `acceptance_status: human_review_required`.

- [ ] Add `test_delivery_acceptance`; run it and confirm the missing-package failure.
- [ ] Initialize with `assets`, implement the inspection workflow, and create the acceptance record.
- [ ] Run targeted/full tests and validation; commit with `feat: add procurement delivery acceptance skill`.

### Task 8: Supplier Evaluation Skill and Script

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `tests/test_evaluate_supplier.py`
- Create: `skills/procurement-supplier-evaluation/SKILL.md`
- Create: `skills/procurement-supplier-evaluation/agents/openai.yaml`
- Create: `skills/procurement-supplier-evaluation/scripts/evaluate_supplier.py`

**Interfaces:**
- Produces: `evaluate_supplier(data: dict) -> dict`.
- Returns: dimension results, evidence coverage, weighted score on a 0–5 scale, performance band, missing evidence, and `decision_status: human_review_required`.

- [ ] Write literal tests for a complete weighted score, partial evidence, evidence-free dimensions, invalid scores, and invalid weights; confirm import failure.
- [ ] Add the structural method and confirm the absent-package failure.
- [ ] Initialize with `scripts`; implement evidence-backed scoring and a JSON CLI without automated renewal or blacklisting.
- [ ] Run behavior/structural/full tests and validation; commit with `feat: add procurement supplier evaluation skill`.

### Task 9: Supplier Database Skill and SQLite Tool

**Files:**
- Modify: `tests/test_procurement_skills.py`
- Create: `tests/test_supplier_db.py`
- Create: `skills/procurement-supplier-database/SKILL.md`
- Create: `skills/procurement-supplier-database/agents/openai.yaml`
- Create: `skills/procurement-supplier-database/scripts/supplier_db.py`
- Create: `skills/procurement-supplier-database/references/supplier_schema.md`

**Interfaces:**
- Produces: `connect_database`, `initialize_database`, `upsert_record`, and `query_record`.
- Supported entities: supplier, qualification, offering, quote, contract, delivery, evaluation; every mutation returns the stored record and `audit_event_id`.

- [ ] Write tests for all tables, one mutation per entity, unique registration/quote/contract IDs, foreign keys, field validation, minimum-field queries, before/after audits, and rollback; confirm import failure.
- [ ] Add the structural method and confirm the absent-package failure.
- [ ] Initialize with `scripts,references`; implement allowlisted parameterized SQLite operations and schema documentation.
- [ ] Run database/structural/full tests and validation; commit with `feat: add procurement supplier database skill`.

### Task 10: Collection Verification and Demonstration

**Files:**
- Modify: `.gitignore` only if disposable database or cache artifacts are not already excluded.

**Interfaces:**
- Consumes: all nine packages and tests.
- Produces: a validated procurement skill collection and fictional end-to-end demonstration output.

- [ ] Run `python3 -m unittest discover -s tests -p 'test_*.py'` and require zero failures.
- [ ] Run `quick_validate.py` on every `skills/procurement-*` directory.
- [ ] Run `git diff --check`, compile scripts, execute each script's `--help`, scan for incomplete placeholders, validate resource references, and check every skill is below 500 words.
- [ ] With fictional data, compare quotations, render an unissued order, evaluate a supplier, initialize a disposable database, write representative records, query minimum fields, and inspect audit events.
- [ ] Review the diff for scope and safety, then commit any final procurement-only corrections.
