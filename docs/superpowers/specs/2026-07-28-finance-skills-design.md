# Finance Skills Design — Current Atomic Catalog

The finance department owns eight atomic Skills:

1. `finance-budget-planning`
2. `finance-budget-check`
3. `finance-expense-request`
4. `finance-expense-review`
5. `finance-invoice-verification`
6. `finance-payment-approval`
7. `finance-accounting`
8. `finance-reporting`

`finance-budget-check` is the reusable budget-availability gate for procurement and finance requests. It checks balance, funding source, budget account, thresholds, and availability but never approves spending. Minimum-field access, stable IDs, restricted evidence references, explicit human confirmation, and append-only audit evidence are enforced inside the relevant workflow Skills.

All packages live under `.agents/skills/`.
