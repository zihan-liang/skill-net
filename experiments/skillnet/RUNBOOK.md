# SkillNet E0/E1 Minimal Experiment Runner

This directory contains the minimal frozen-condition runner and deterministic
verification wrapper for E0/E1. Creating this setup does **not** run GT01–GT21.

## Frozen runtime

The setup was created on repository commit
`0c1adbc06838dc1284b2eec42d3572867dedfd76` with:

- Codex CLI: `codex-cli 0.146.0-alpha.3.1`
- Codex executable:
  `/Applications/ChatGPT.app/Contents/Resources/codex`
- model: `gpt-5.6-sol`
- `model_reasoning_effort`: `high`
- execution order: serial
- model attempts per task: one
- automatic retries: none

`run_condition.py` passes the model and reasoning values explicitly while using
`--ignore-user-config`; it refuses a real run if the installed CLI version no
longer matches the frozen version. This keeps A/B/C and all sizes on the same
runtime settings.

The CLI options above were confirmed from the installed `codex exec --help`.
The real child command uses only supported flags:
`--ignore-user-config`, `--ignore-rules`, `--strict-config`, `--ephemeral`,
`--skip-git-repo-check`, `--sandbox read-only`, `--model`, `--config`,
`--output-schema`, `--cd`, and `--output-last-message`.

## Isolation contract

Every task starts a new `codex exec` process in a fresh temporary working
directory. The user configuration and project rules are ignored. The temporary
packet contains only a fixed, enum-free JSON output schema; the child prompt
contains only:

1. the current Chinese task;
2. the one Catalogue selected for the current condition;
3. fixed JSON output and no-tool instructions.

The child is explicitly forbidden from using tools or reading files. It is not
given Gold, the evaluator, `.agents/skills/`, `SKILL.md`, a relation file,
another Catalogue, another task, or an earlier response. C uses only the
relations already embedded in its Catalogue.

The fixed child output schema does not enumerate the full 46-Skill universe, so
small conditions do not learn IDs outside their Catalogue. After the response,
the unchanged canonical
`SkillNet_Gold_Tasks_V4/evaluation/prediction_schema.json` performs the actual
schema validation.

## Condition mapping

- E0 is fixed to size 46 and GT01–GT21.
- E1 uses exactly the five task IDs in
  `skillnet_run_guide_v1_1/E1_scale_manifest.json`.
- A selects `A_flat_catalogue.json`.
- B selects `B_department_grouped_catalogue.json`.
- C selects `C_graph_structured_catalogue.json`; no separate relation file is
  read or passed.

Run output is stored at:

```text
experiments/skillnet/runs/<experiment>/<configuration>/size_<size>/<run_id>/
```

Each task directory records:

- `raw_response.txt`;
- `prediction.json` only when the raw response itself is directly parseable and
  valid under the canonical schema;
- `schema_validation.json`;
- `run_metadata.json`.

An existing run is never overwritten. `--resume` only visits task directories
that have never produced `raw_response.txt`; an existing raw response is never
retried or replaced.

## Formal run commands

Use a unique `run_id` for every condition.

E0:

```bash
python3 experiments/skillnet/run_condition.py --experiment E0 --configuration A --size 46 --run-id e0_a_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E0 --configuration B --size 46 --run-id e0_b_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E0 --configuration C --size 46 --run-id e0_c_r01 --execute
```

E1 size 10:

```bash
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration A --size 10 --run-id e1_s10_a_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration B --size 10 --run-id e1_s10_b_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration C --size 10 --run-id e1_s10_c_r01 --execute
```

E1 size 30:

```bash
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration A --size 30 --run-id e1_s30_a_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration B --size 30 --run-id e1_s30_b_r01 --execute
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration C --size 30 --run-id e1_s30_c_r01 --execute
```

E1 size 46 is also supported with `--size 46`.

Resume example:

```bash
python3 experiments/skillnet/run_condition.py --experiment E1 --configuration A --size 10 --run-id e1_s10_a_r01 --execute --resume
```

## Deterministic verification

`verify_condition.py` ignores any saved `prediction.json` and mechanically
extracts the final JSON object again from each immutable `raw_response.txt`. It
does not correct fields, IDs, order, status, or meaning. Only extracted objects
that pass the canonical prediction schema and match their task ID are copied
into the dedicated evaluator predictions directory.

That predictions directory contains prediction JSON files only. Metadata,
validation records, commands, stdout, stderr, and evaluator results live
outside it.

Example:

```bash
python3 experiments/skillnet/verify_condition.py --experiment E0 --configuration A --size 46 --run-id e0_a_r01
```

The script prints and saves a standalone line beginning with
`VERIFY COMMAND:`. Verification results are stored at:

```text
experiments/skillnet/results/<experiment>/<configuration>/size_<size>/<run_id>/
```

E0 verification uses the canonical 21-task Gold. E1 verification always uses
`experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json`, never the full
21-task Gold.

## Frozen E1 Gold

The five-task file is mechanically extracted with:

```bash
python3 experiments/skillnet/verify_condition.py --prepare-e1-gold
```

The file preserves all five task records byte-for-byte at the JSON-value level,
retains the full evaluator metadata/catalogue fields, sets `task_count` to five,
and records the full Gold hash, manifest hash, and manifest task IDs. The
existing evaluator validates the resulting package.

## Fixture-only SETUP mode

`--fixture-response-dir <directory>` replaces `--execute` for setup tests. It
copies static `<task_id>.txt` responses and never starts Codex. Runs created in
this mode record `execution_mode: fixture` and must not be used as experimental
results.
