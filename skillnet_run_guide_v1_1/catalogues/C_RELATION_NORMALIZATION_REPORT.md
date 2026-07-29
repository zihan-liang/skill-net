# C Relation Normalization Report

Source commit: `742e39d837484e5311e6663658bc7420c2a07a6b`

SHA-256 sources:

- `skill_relations.json`: `7870d51ae4855787f9f32991d77bdd57509c35b9093c21de08f48402df86a590`
- `skill_relations_10.json`: `3af80d5c2cdd6a09464d57f699c809129f83d1a72d06cb74aebf95899f9e3f6d`
- `skill_relations_30.json`: `ebb3af1379e1e135940a08fc3552cc0edbe4d60a94a2818d3dc768173dcb3388`
- `skill_relations_46.json`: `7870d51ae4855787f9f32991d77bdd57509c35b9093c21de08f48402df86a590`

## Normalization contract

- Department membership is represented by the same B/C department grouping. It expresses ownership only.
- `prerequisite` preserves `before`, `after`, `scope`, and preserves `condition` only when the source has it.
- `conflict.skills[0]` becomes `gate_skill`; `conflict.skills[1]` becomes `blocked_skill`; `condition` is preserved. Direction is unchanged.
- `mutex.skills[0:2]` becomes `skill_a` / `skill_b`; `context` is preserved.
- `enhances` preserves `source`, `target`, and `context`.
- No new executable hierarchy, route container, or expansion relation is introduced.

## Closure and one-to-one proof

| Size | source department records | represented memberships | prerequisite | conflict | mutex | enhances | filtered root equals scale source |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 10 | 4 | 10 | 6 | 2 | 0 | 1 | yes |
| 30 | 5 | 30 | 25 | 7 | 0 | 4 | yes |
| 46 | 5 | 46 | 53 | 13 | 4 | 13 | yes |

For every size, each source relation array is normalized item-by-item without filtering, synthesis, or deduplication. Counts are equal before and after normalization, and reversing the field mapping reproduces the same endpoints, condition/scope, and context.

The size-10 source has four populated department records; the formal B/C Catalogue still lists all five canonical departments, with the finance group empty. The ten represented Skill memberships exactly equal the source membership set.

## Examples

### prerequisite

```json
{
  "before": "finance-budget-planning",
  "after": "finance-budget-check",
  "scope": "finance"
}
```

The formal entry keeps the same fields; no missing condition is invented.

### directional conflict

Source:

```json
{
  "skills": [
    "finance-budget-check",
    "procurement-purchase-order"
  ],
  "condition": "budget_not_approved"
}
```

Formal C:

```json
{
  "gate_skill": "finance-budget-check",
  "blocked_skill": "procurement-purchase-order",
  "condition": "budget_not_approved"
}
```

### mutex

Source:

```json
{
  "skills": [
    "finance-expense-request",
    "procurement-requirement"
  ],
  "context": "same_expense"
}
```

Formal C:

```json
{
  "skill_a": "finance-expense-request",
  "skill_b": "procurement-requirement",
  "context": "same_expense"
}
```

### enhances

Source and formal C retain the same `source`, `target`, and `context`; only the enclosing experiment view changes.

## Conclusion

No source relation is lost. The existing size files are semantically identical to filtering the latest root relation file by their frozen node sets, so `build_scaled_relations.py` was not used to replace them. Formal C changes field clarity only and introduces no S3-style high-level entity or expansion semantics.
