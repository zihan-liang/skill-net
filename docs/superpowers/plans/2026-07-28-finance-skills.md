# Finance Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify eight composable Codex skills for the finance workflow and its auditable demonstration database.

**Architecture:** Keep each workflow node in an independent `skills/finance-*` package with concise instructions and generated UI metadata. Use Markdown assets for human-reviewed forms and Python standard-library scripts for invoice arithmetic, balanced journals, reporting calculations, and transactional SQLite storage.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, SQLite, Codex `skill-creator` initialization and validation scripts.

## Global Constraints

- Keep every `SKILL.md` below 500 words with only `name` and trigger-oriented `description` frontmatter.
- Include Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes.
- Include an English workflow and a `**中文摘要：**` line in each skill.
- Require authorized human approval for budget activation, expense decisions, payment release, journal posting, period close, and report publication.
- Never execute payments, post to a live ledger, submit filings, or claim external invoice-authenticity verification.
- Use `Decimal` for monetary arithmetic and explicit currencies for every monetary record.
- Record database mutations with actor, business purpose, evidence reference, before/after values, and UTC timestamp.
- Create every skill through `skill-creator/scripts/init_skill.py` and validate every package with `quick_validate.py`.

---

### Task 1: Budget Planning Skill

**Files:**
- Create: `tests/test_finance_skills.py`
- Create: `skills/finance-budget-planning/SKILL.md`
- Create: `skills/finance-budget-planning/agents/openai.yaml`
- Create: `skills/finance-budget-planning/assets/budget_template.md`

**Interfaces:**
- Consumes: strategy assumptions, `department_id`, period, currency, budget owner, revenue lines, expense lines, contingency, approval route.
- Produces: `budget_id`, version, totals, assumptions, variance risks, missing information, `approval_status: draft`.

- [ ] **Step 1: Write the failing structural test**

Create a `unittest` contract whose `test_budget_planning` calls `validate_skill("finance-budget-planning")`. Validate metadata, required headings, Chinese summary, human decision boundary, resource references, word count, and `$finance-budget-planning` in `agents/openai.yaml`.

- [ ] **Step 2: Verify the test fails for the absent package**

Run: `python3 -m unittest tests.test_finance_skills.FinanceSkillContractTests.test_budget_planning`

Expected: FAIL because `skills/finance-budget-planning/SKILL.md` does not exist.

- [ ] **Step 3: Initialize and implement the package**

Run `init_skill.py finance-budget-planning --path skills --resources assets` with interface values for display name, short description, and a default prompt invoking `$finance-budget-planning`. Replace generated placeholder content with the approved workflow and create the complete budget template.

- [ ] **Step 4: Verify green and commit the skill**

Run the targeted unittest and `quick_validate.py skills/finance-budget-planning`. Commit the test and package with `feat: add finance budget planning skill`.

### Task 2: Expense Request Skill

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `skills/finance-expense-request/SKILL.md`
- Create: `skills/finance-expense-request/agents/openai.yaml`
- Create: `skills/finance-expense-request/assets/expense_request_template.md`

**Interfaces:**
- Consumes: requester, purpose, supplier, amount, currency, budget reference, due date, supporting-document references.
- Produces: `expense_id`, normalized request packet, missing evidence, duplicate indicators, and `submission_status: draft`.

- [ ] **Step 1: Add and fail the targeted contract**

Add `test_expense_request`, run only that test, and confirm it fails because the package is absent.

- [ ] **Step 2: Initialize and implement the package**

Use `init_skill.py` with `assets`, generate `agents/openai.yaml`, replace the generated skill, and create the expense request template with stable identifiers and explicit currency.

- [ ] **Step 3: Validate and commit**

Run the targeted test, official validator, and full suite. Commit with `feat: add finance expense request skill`.

### Task 3: Expense Review Skill

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `skills/finance-expense-review/SKILL.md`
- Create: `skills/finance-expense-review/agents/openai.yaml`

**Interfaces:**
- Consumes: expense packet, policy reference, budget availability, reviewer identity, conflict declaration.
- Produces: review checks, exceptions, segregation-of-duties result, recommendation, and `decision_status: human_review_required`.

- [ ] **Step 1: Add and fail the targeted contract**

Add `test_expense_review`, run it, and confirm the missing-package failure.

- [ ] **Step 2: Initialize and implement the package**

Use `init_skill.py` without resource folders. Encode policy, budget, evidence, duplicate, conflict, and approval checks while reserving the decision for an authorized reviewer.

- [ ] **Step 3: Validate and commit**

Run the targeted test, official validator, and full suite. Commit with `feat: add finance expense review skill`.

### Task 4: Invoice Verification Skill and Script

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `tests/test_verify_invoice.py`
- Create: `skills/finance-invoice-verification/SKILL.md`
- Create: `skills/finance-invoice-verification/agents/openai.yaml`
- Create: `skills/finance-invoice-verification/scripts/verify_invoice.py`

**Interfaces:**
- Produces: `verify_invoice(invoice: dict, expense_request: dict, existing_keys: list[str]) -> dict`.
- Output fields: invoice ID, arithmetic status, request-match status, duplicate status, discrepancies, `authenticity_status: not_verified`, and `decision_status: human_review_required`.

- [ ] **Step 1: Write behavior tests before the script**

Test a matching invoice with hand-calculated `100.00 + 6.00 = 106.00`, a mismatched total, missing fields, currency mismatch, supplier mismatch, and duplicate key `SUP-1|INV-1`.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest tests.test_verify_invoice`

Expected: import failure because the script is absent.

- [ ] **Step 3: Implement the minimal script and package**

Use `Decimal`, reject invalid or negative monetary inputs, normalize the duplicate key, return auditable discrepancies, and expose a JSON CLI. Initialize the skill with `scripts` and document the script workflow.

- [ ] **Step 4: Verify and commit**

Run behavior tests, the targeted skill contract, official validator, and full suite. Commit with `feat: add finance invoice verification skill`.

### Task 5: Payment Approval Skill

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `skills/finance-payment-approval/SKILL.md`
- Create: `skills/finance-payment-approval/agents/openai.yaml`
- Create: `skills/finance-payment-approval/assets/payment_approval_template.md`

**Interfaces:**
- Consumes: approved expense review, invoice validation, payee verification reference, due date, amount, currency, approver identities.
- Produces: `payment_id`, approval packet, blocking checks, approval route, `release_status: not_released`, and `communication_status: draft`.

- [ ] **Step 1: Add and fail the targeted contract**

Add `test_payment_approval`, run it, and confirm the missing-package failure.

- [ ] **Step 2: Initialize and implement the package**

Use `init_skill.py` with `assets`. Create the approval template and enforce segregation of requester, reviewer, and payment releaser roles.

- [ ] **Step 3: Validate and commit**

Run the targeted test, official validator, and full suite. Commit with `feat: add finance payment approval skill`.

### Task 6: Accounting Skill and Journal Validator

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `tests/test_validate_journal.py`
- Create: `skills/finance-accounting/SKILL.md`
- Create: `skills/finance-accounting/agents/openai.yaml`
- Create: `skills/finance-accounting/scripts/validate_journal.py`

**Interfaces:**
- Produces: `validate_journal(entry: dict) -> dict`.
- Output fields: journal ID, line count, debit total, credit total, currency, balanced flag, validation status, `posting_status: draft`, and `decision_status: human_approval_required`.

- [ ] **Step 1: Write and fail behavior tests**

Use literal fixtures for a balanced two-line entry and assert failures for unequal totals, negative values, dual-sided lines, mixed currencies, missing source evidence, and a closed period.

- [ ] **Step 2: Implement the minimal validator and package**

Use `Decimal`, require at least two lines, exactly one positive side per line, a single currency, an open period, and a source reference. Add a JSON CLI and skill instructions.

- [ ] **Step 3: Verify and commit**

Run behavior tests, the targeted contract, official validator, and full suite. Commit with `feat: add finance accounting skill`.

### Task 7: Reporting Skill and Generator

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `tests/test_financial_reporting.py`
- Create: `skills/finance-reporting/SKILL.md`
- Create: `skills/finance-reporting/agents/openai.yaml`
- Create: `skills/finance-reporting/scripts/generate_financial_report.py`

**Interfaces:**
- Produces: `generate_report(data: dict) -> dict`.
- Output fields: report ID, period, currency, budget total, expense actual, budget variance, income, expense, net movement, opening/expected/actual closing cash, reconciliation difference, receivables, payables, evidence coverage, and report status.

- [ ] **Step 1: Write and fail behavior tests**

Use hand-calculated fixtures to assert budget variance, income and expense totals, open receivables/payables, cash reconciliation, source coverage, status, and currency-mismatch rejection.

- [ ] **Step 2: Implement the minimal generator and package**

Use only approved/posted/paid records in recognized totals, sum open/overdue items, quantify coverage, mark unreconciled or incomplete output as draft, and expose a JSON CLI.

- [ ] **Step 3: Verify and commit**

Run behavior tests, the targeted contract, official validator, and full suite. Commit with `feat: add finance reporting skill`.

### Task 8: Finance Database Skill and SQLite Tool

**Files:**
- Modify: `tests/test_finance_skills.py`
- Create: `tests/test_finance_db.py`
- Create: `skills/finance-database/SKILL.md`
- Create: `skills/finance-database/agents/openai.yaml`
- Create: `skills/finance-database/scripts/finance_db.py`
- Create: `skills/finance-database/references/finance_schema.md`

**Interfaces:**
- Produces: `connect_database`, `initialize_database`, `upsert_record`, and `query_record`.
- Supported entities: department, budget, transaction, invoice, payment, open item, and report snapshot.
- Every `upsert_record` returns the stored record plus `audit_event_id`.

- [ ] **Step 1: Write and fail database tests**

Assert all required tables exist. Insert one record for each supported entity, verify audit metadata, reject duplicate invoice keys, reject invalid amounts/currencies/kinds, preserve rollback on failure, and return only requested query fields.

- [ ] **Step 2: Implement the SQLite tool and schema reference**

Use explicit table/field allowlists, parameterized SQL, transactions, stable IDs, foreign keys, unique invoice keys, and append-only audit events. Add CLI commands for `init`, `upsert`, and minimum-field `query`.

- [ ] **Step 3: Implement and validate the package**

Initialize with `scripts,references`, document authorization and mutation confirmation, run database tests, the targeted contract, official validator, and full suite.

- [ ] **Step 4: Commit**

Commit with `feat: add finance database skill`.

### Task 9: Collection Verification and Demonstration

**Files:**
- Modify: `.gitignore` only if generated database or cache artifacts are not already covered.

**Interfaces:**
- Consumes: all eight packages and tests.
- Produces: validated skill collection and a disposable end-to-end demonstration output.

- [ ] **Step 1: Run all tests**

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`

Expected: all HR and finance tests pass with zero failures.

- [ ] **Step 2: Run official package validation**

Run `quick_validate.py` for every `skills/finance-*` directory with the validator's Python dependency path configured.

- [ ] **Step 3: Run quality checks**

Run `git diff --check`, compile each Python script, execute each script's `--help`, scan for incomplete placeholder markers, verify resource references, and confirm each `SKILL.md` is below 500 words.

- [ ] **Step 4: Exercise the workflow safely**

Use fictional consumer-platform data to validate an invoice, balance a journal, generate a report, initialize a disposable SQLite database, insert representative records, query minimum fields, and confirm audit events. Do not contact any external system or move money.

- [ ] **Step 5: Commit the completed collection**

Stage only finance skill, test, plan, and any necessary ignore files. Commit with `feat: add finance workflow skills`.
