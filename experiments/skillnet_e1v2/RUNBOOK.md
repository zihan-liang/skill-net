# SkillNet E1-v2 Setup and Later Run Contract

Experiment ID: `E1V2`

This namespace implements task-conditioned, nested candidate pools for the same
frozen task and Gold at sizes 10, 30, and 46. Setup creates no formal model
prediction. It is isolated from `experiments/skillnet/`, all E0/E1 Catalogues,
Gold, runners, results, and `run_01`/`run_02`.

## Frozen task set

E1-v2 contains the 18 original tasks whose complete GoldRelevantSkills union
fits size 10. Original GT03, GT07, and GT12 are excluded and represented by
three new IDs:

- `E1V2_GT03_PROC_SHORT`
- `E1V2_GT07_CUSTOM_TECH_SUPPLIER_SHORT`
- `E1V2_GT12_BUSINESS_TO_PO_SHORT`

The source-to-E1-v2 mapping and every GoldRelevantSkills source field are frozen
in `skillnet_run_guide_v1_1/e1v2_catalogues/candidate_pool_manifest.json`.

## Deterministic Setup generation

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  experiments/skillnet_e1v2/build_setup.py

PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  experiments/skillnet_e1v2/build_setup.py --check
```

`--check` compares every generated JSON/text byte sequence and never rewrites
it. The builder stops if any task has more than ten GoldRelevantSkills.

For each task, the frozen ordering is all alphabetically sorted
GoldRelevantSkills followed by non-Gold Skills ranked with a fixed score:
same-department similarity, frozen-graph adjacency, lifecycle over-call risk,
canonical-ID token similarity, and task-text department keywords. Ties use
ascending canonical Skill ID. S10 is the first 10, S30 the first 30, and S46
all 46. No post-result adjustment is allowed.

## Catalogue isolation and fairness

Each task/size has one A, B, and C Catalogue under:

```text
skillnet_run_guide_v1_1/e1v2_catalogues/tasks/<task_id>/size_<size>/
```

- A is flat and has no department containers or relations.
- B groups the identical cards by canonical department and has no relations.
- C has B's identical department/card JSON values plus the complete induced
  subgraph of the frozen 46-Skill C Catalogue.

Children receive only the Chinese task, the one current Catalogue, and the
fixed eight-field contract. Gold, evaluator, other tasks, other sizes,
standalone relations, prior results, and repository Skills remain hidden.

## Fixed route/status contract

The child prompt only permits `{}`, the two canonical acceptance-route objects,
and the two canonical build-or-buy objects. It explicitly defines completed,
blocked, no-tool, future-step handling, sequence exclusions, and upstream-only
`blocked_by`. The eight-field schema wrapper changes only the task-ID pattern
needed for the three new task IDs.

Semantic aliases are global and frozen in
`experiments/skillnet_e1v2/semantic_normalization.json`. Metric definitions are
frozen in `experiments/skillnet_e1v2/metric_definitions.json`. Neither permits
task-specific post-run exceptions.

## Setup-only fixture dry run

This uses static Gold-perfect JSON and a temporary state root. It starts no
Codex process and writes no formal result:

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  -m unittest discover -s experiments/skillnet_e1v2/tests -v
```

## Synthetic live smoke

This is one non-benchmark Codex process with an empty temporary working
directory, no Gold, and no Catalogue:

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  experiments/skillnet_e1v2/synthetic_smoke.py --smoke-id setup_01
```

It is not a formal E1-v2 task. The command, event bytes, raw response, stderr,
prompt, and deterministic validation are retained under
`experiments/skillnet_e1v2/setup_evidence/synthetic_smoke/setup_01/`.

## Later formal execution (not authorized in this Setup)

`run_condition.py --execute` is provided for later human review. Do not run it
until the frozen Setup is reviewed and separately authorized. Every condition
will use 21 fresh, one-shot child processes and an unused run ID.

Fixture example:

```bash
state_root="$(mktemp -d)"
experiments/skillnet/.venv/bin/python \
  experiments/skillnet_e1v2/run_condition.py \
  --configuration A --size 10 --run-id fixture_review \
  --fixture-response-dir experiments/skillnet_e1v2/fixtures/gold_perfect \
  --state-root "$state_root"
experiments/skillnet/.venv/bin/python \
  experiments/skillnet_e1v2/verify_condition.py \
  --configuration A --size 10 --run-id fixture_review \
  --state-root "$state_root"
```

Formal outputs, when later authorized, belong only below
`experiments/skillnet_e1v2/runs/E1V2/` and
`experiments/skillnet_e1v2/results/E1V2/`.
