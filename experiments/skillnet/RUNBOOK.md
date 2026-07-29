# SkillNet E0/E1 Minimal Experiment Runner

This directory contains the minimal frozen-condition runner and deterministic
verification wrapper for E0/E1. Creating or validating this setup does **not**
run GT01–GT21.

## Frozen runtime

This Setup repair was developed from repository commit
`8870a12e81a3aa3ef7112a14c976449666a73698` with:

- Codex CLI: `codex-cli 0.146.0-alpha.3.1`
- Codex executable:
  `/Applications/ChatGPT.app/Contents/Resources/codex`
- model: `gpt-5.6-sol`
- `model_reasoning_effort`: `high`
- Python: `3.9.6`
- `jsonschema`: `4.25.1`
- execution order: serial
- runner attempts per task: one fresh `codex exec` process
- runner-level automatic retries: none
- transport reconnects inside that one `codex exec` process: allowed

`run_condition.py` passes the model and reasoning values explicitly while using
`--ignore-user-config`; it refuses a real run if the installed CLI version no
longer matches the frozen version. It records the Python executable, Python
version, and `jsonschema` version in condition metadata. This keeps A/B/C and
all sizes on the same recorded runtime settings.

The CLI options above were confirmed from the installed `codex exec --help`.
The real child command uses only supported flags:
`--ignore-user-config`, `--ignore-rules`, `--strict-config`, `--ephemeral`,
`--skip-git-repo-check`, `--sandbox read-only`, `--model`, `--config`,
`--cd`, and `--output-last-message`.

The CLI may reconnect its transport within the same process. Such a reconnect
does not start a second model attempt. A model attempt is defined here as one
fresh `codex exec` process. The runner never starts a replacement process for a
failed task and formal runs never use `--resume`.

## Python environment

Create the ignored experiment virtual environment once during Setup:

```bash
/Library/Developer/CommandLineTools/usr/bin/python3 -m venv experiments/skillnet/.venv
experiments/skillnet/.venv/bin/python -m pip install -r experiments/skillnet/requirements.txt
experiments/skillnet/.venv/bin/python --version
experiments/skillnet/.venv/bin/python -c 'import importlib.metadata; print(importlib.metadata.version("jsonschema"))'
```

The final two commands must print `Python 3.9.6` and `4.25.1`. Use
`experiments/skillnet/.venv/bin/python` for every runner and verifier command.

## Isolation contract

Every task starts a new `codex exec` process in a fresh temporary working
directory. The user configuration and project rules are ignored. The temporary
working directory starts empty; the child prompt contains only:

1. the current Chinese task;
2. the one Catalogue selected for the current condition;
3. fixed JSON output and no-tool instructions.

The child is explicitly forbidden from using tools or reading files. It is not
given Gold, the evaluator, `.agents/skills/`, `SKILL.md`, a relation file,
another Catalogue, another task, or an earlier response. C uses only the
relations already embedded in its Catalogue.

The fixed prompt contract enumerates only the eight field names, primitive
types, and status-consistency rules. It does not enumerate the full 46-Skill
universe, so small conditions do not learn IDs outside their Catalogue. The CLI
transport schema is intentionally not used because the canonical schema relies
on unsupported Structured Outputs keywords and has a dynamic `route_choice`
object. After the raw response is produced, the unchanged canonical
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

An existing run is never overwritten. The runner still exposes `--resume` for
non-formal recovery diagnostics, but it is prohibited for formal E0/E1 runs.
An existing raw response is never retried or replaced.

## Formal preflight

Before every formal condition, confirm all of the following and stop on drift:

1. `git rev-parse HEAD` equals `git rev-parse origin/main`.
2. `git status --short --untracked-files=all` is empty.
3. Catalogue validation and frozen E1 Gold validation are still successful.
4. the Codex path/version, model, reasoning effort, Python, and `jsonschema`
   values match the frozen runtime above;
5. the fixture dry run and synthetic live smoke test below passed;
6. no Skill, Gold, Catalogue, relations, canonical schema, or evaluator file
   changed after validation.

The failed `run_01` directories are audit evidence and must not be deleted,
overwritten, repaired, or resumed. After this Setup repair is committed and
`origin/main` matches it, use a new run ID such as `run_02`.

## Formal run commands

Use a new `run_id` generation for the experiment. The same value may be reused
across conditions because the condition is part of the output path. The examples
below use `run_02`; do not reuse the failed `run_01` artifacts.

E0:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E0 --configuration A --size 46 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E0 --configuration B --size 46 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E0 --configuration C --size 46 --run-id run_02 --execute
```

E1 size 10:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration A --size 10 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration B --size 10 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration C --size 10 --run-id run_02 --execute
```

E1 size 30:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration A --size 30 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration B --size 30 --run-id run_02 --execute
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py --experiment E1 --configuration C --size 30 --run-id run_02 --execute
```

E1 size 46 is extracted from the corresponding E0 `run_02` outputs and does not
start new model processes. Do not run E1 with `--size 46` during the formal
sequence and do not use `--resume`.

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
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py --experiment E0 --configuration A --size 46 --run-id run_02
```

The script prints and saves a standalone line beginning with
`VERIFY COMMAND:`. It records the actual `sys.executable`, so verification is
replayed with the same fixed virtual environment. Verification results are
stored at:

```text
experiments/skillnet/results/<experiment>/<configuration>/size_<size>/<run_id>/
```

E0 verification uses the canonical 21-task Gold. E1 verification always uses
`experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json`, never the full
21-task Gold.

## Frozen E1 Gold

The five-task file is mechanically extracted with:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py --prepare-e1-gold
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

Run it under a temporary `--state-root`, then run `verify_condition.py` against
the same temporary state. Do not place Setup output under the formal `runs/` or
`results/` trees.

## Synthetic live SETUP smoke test

Before formal execution, start exactly one fresh `codex exec` process with the
frozen CLI/model/reasoning flags, an empty temporary `--cd`, and a synthetic
prompt that contains neither a Gold task nor any Catalogue. Do not pass
`--output-schema`. Require exit code zero and a directly parseable JSON object
with exactly these keys:

```text
task_id, use_skills, selected_departments, skill_sequence,
final_status, blocked_by, route_choice, reason
```

The synthetic prompt must repeat the same three status-consistency rules used
by the runner. Validate those rules as well as the exact key set. A smoke output
with inconsistent `use_skills`, `final_status`, or `blocked_by` values is a
failed Setup attempt even when transport and JSON parsing succeeded; preserve
it and use a new synthetic smoke ID after correcting the Setup instruction.

Transport reconnect messages are allowed provided they occur inside that same
process. Preserve the smoke command, stdout, stderr, raw response, and validation
result as Setup evidence; never treat the response as experimental data.
