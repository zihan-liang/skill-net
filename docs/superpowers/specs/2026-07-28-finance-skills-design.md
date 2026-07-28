# Finance Skills Design

## Goal

Create eight independent, composable Codex skills for the finance workflow of the AI Agent-driven consumer partner platform. Seven skills cover the operating sequence from budgeting through reporting; one provides a privacy-minimized, auditable finance database for budgets, income and expenses, invoices, payments, receivables, payables, and generated reports.

## Architecture

Use one skill package per workflow node so Codex can trigger only the relevant instructions and resources. Human reviewers retain authority over budgets, expenses, payments, accounting entries, and published reports. Deterministic Python scripts handle arithmetic, structural validation, duplicate checks, balanced-journal validation, reporting calculations, and SQLite mutations.

The primary flow is:

`finance-budget-planning` → `finance-expense-request` → `finance-expense-review` → `finance-invoice-verification` → `finance-payment-approval` → `finance-accounting` → `finance-reporting`

`finance-database` supports every stage and records each confirmed mutation in an append-only audit log.

## Packages

1. `finance-budget-planning`
   - Convert strategy and operating assumptions into versioned departmental budgets.
   - Use `assets/budget_template.md` for period, owner, revenue, expense, contingency, assumptions, and approval fields.
   - Output a draft budget and approval route; never mark it approved without evidence.
2. `finance-expense-request`
   - Convert an employee or department request into a complete, traceable expense packet.
   - Use `assets/expense_request_template.md` for purpose, supplier, amount, currency, budget line, dates, attachments, and requester declaration.
   - Reject missing business purpose, budget reference, or evidence from the ready-for-review queue.
3. `finance-expense-review`
   - Check policy eligibility, budget availability, supporting evidence, duplicate risk, conflicts, and segregation of duties.
   - Produce findings and a human-review recommendation without approving or rejecting automatically.
4. `finance-invoice-verification`
   - Use `scripts/verify_invoice.py` to validate required invoice fields, recompute subtotal/tax/total, compare invoice and request amounts, and detect duplicate invoice keys supplied in prior records.
   - Clearly distinguish data-consistency validation from tax-authority authenticity verification.
5. `finance-payment-approval`
   - Assemble an approval-ready payment packet after expense and invoice review.
   - Use `assets/payment_approval_template.md` for payee, bank-detail verification status, amount, due date, evidence, approvers, and segregation-of-duties checks.
   - Never execute, schedule, or claim completion of a real payment.
6. `finance-accounting`
   - Translate an approved business event into a proposed journal entry.
   - Use `scripts/validate_journal.py` to require at least two lines, valid debit/credit amounts, a balanced entry, one currency, an open period, and source evidence.
   - Keep account selection and posting under authorized accountant control.
7. `finance-reporting`
   - Use `scripts/generate_financial_report.py` to aggregate approved period data into budget-versus-actual, income/expense, cash movement, receivables, and payables summaries.
   - Report source coverage and reconciliation differences; label unreconciled output as draft.
8. `finance-database`
   - Use `scripts/finance_db.py` and `references/finance_schema.md` for controlled SQLite operations.
   - Store departments, budget versions and lines, income/expense transactions, invoices, payments, receivables/payables, report snapshots, and audit events.
   - Require stable IDs, an authorized actor, a stated business purpose, source evidence for mutations, and minimum-necessary query results.

## Common Skill Contract

Each package contains a `SKILL.md` with only `name` and a trigger-oriented `description` in YAML frontmatter. The body remains concise and contains: Overview, Required Inputs, Workflow, Output Contract, SkillNet Relationships, Guardrails, Example, and Common Mistakes. Each body includes an English workflow and a Chinese summary. Each package also contains `agents/openai.yaml` with a human-readable name, concise description, and a default prompt that explicitly invokes the corresponding `$finance-*` skill.

## Data Flow and Statuses

- Stable identifiers link `budget_id`, `expense_id`, `invoice_id`, `payment_id`, `journal_id`, and `report_id`.
- Every downstream step consumes the latest approved upstream version and preserves its source identifier.
- Standard statuses distinguish `draft`, `pending_review`, `approved`, `rejected`, `posted`, `paid`, and `void` without treating recommendations as decisions.
- Currency is explicit on every monetary record. Cross-currency aggregation is prohibited unless approved exchange-rate evidence is supplied.
- Corrections use reversal or new-version records; audit entries are append-only.

## Database Boundaries

The database is a local demonstration implementation, not an ERP or banking integration. It stores only fields required for the stated finance purpose. Supplier banking data is represented by verification status and a restricted reference, not raw bank credentials. Invoice images, contracts, identity documents, credentials, tokens, and private keys are not stored in general-purpose tables.

Every mutation records actor, action, entity type, entity ID, before/after JSON, evidence reference, business purpose, and UTC timestamp. Query responses return only requested fields wherever possible.

## Safety and Control Boundaries

- Require authorized human approval for budget activation, expense decisions, payment release, journal posting, period close, and report publication.
- Enforce segregation of duties: a requester cannot be the sole reviewer and payment releaser for the same transaction.
- Do not invent invoices, approvals, supplier details, exchange rates, tax treatments, accounting accounts, or payment status.
- Do not send bank instructions, execute payments, post entries to a live ledger, submit tax filings, or publish external financial statements.
- Treat invoice checks as arithmetic and record-consistency validation unless an authorized external verification source is explicitly available.
- Surface duplicates, mismatches, missing evidence, closed periods, unbalanced entries, and reconciliation gaps as blocking findings.
- Keep legal, tax, statutory, and accounting-policy decisions with qualified authorized humans.

## Error Handling

Scripts fail closed on missing identifiers, invalid money values, inconsistent currency, duplicate records, unbalanced journals, and unsupported operations. Errors identify the affected field or invariant without exposing unrelated finance data. Database mutations use transactions so failed validation does not leave partial records.

## Testing Strategy

- Add `tests/test_finance_skills.py` first and confirm it fails while the eight packages are absent.
- Add behavior tests before each script:
  - `tests/test_verify_invoice.py` covers valid totals, mismatches, missing fields, and duplicate keys.
  - `tests/test_validate_journal.py` covers balanced entries, unbalanced entries, invalid lines, currency mismatch, and closed periods.
  - `tests/test_financial_reporting.py` covers budget variance, income/expense totals, receivables/payables, and unreconciled status.
  - `tests/test_finance_db.py` covers schema initialization, audited mutations, duplicate protection, minimum queries, and rollback on invalid data.
- Run the full unittest suite after every resource is green.
- Run the official Codex `quick_validate.py` validator on all eight packages.
- Scan skills, tests, and documentation for placeholder text and verify every referenced resource exists.

## Non-Goals

- Live bank, ERP, payment-provider, tax-authority, or invoice-platform integrations
- Jurisdiction-specific tax or statutory accounting advice
- Payroll, procurement, reimbursement-policy authoring, investment management, or fundraising workflows
- Automated approval, payment execution, journal posting, period close, or external report publication

## Success Criteria

- All eight packages are discoverable, concise Codex skills with valid metadata.
- The workflow relationships and human decision boundaries are explicit.
- Deterministic scripts reject unsafe or inconsistent inputs and pass their behavior tests.
- The finance database represents all user-requested record categories with audited mutations.
- Existing HR tests and all new finance tests pass together.
