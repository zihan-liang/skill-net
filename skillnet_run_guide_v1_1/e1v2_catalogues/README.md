# SkillNet E1-v2 Task-Conditioned Catalogues

This directory is independent of the frozen E0/E1 Catalogues.

- `candidate_pool_manifest.json` freezes every task's ordered S10/S30/S46,
  distractor reasons, Gold/task hashes, and GoldRelevantSkills sources.
- `catalogue_manifest.json` records all 189 Catalogue file hashes.
- `candidate_pool_validation_report.json` and
  `catalogue_validation_report.json` are the deterministic Setup gates.
- `tasks/<task_id>/size_<size>/` contains A/B/C.

All task/size C relations are exact induced subgraphs of the existing frozen
size-46 graph Catalogue. A/B contain neither `relations` nor
`relation_semantics`.
