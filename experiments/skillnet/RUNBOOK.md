# SkillNet E0/E1 Minimal Experiment Runner

This directory contains the minimal frozen-condition runner and deterministic
verification wrapper for E0/E1. Creating or validating this setup does **not**
run GT01–GT21.

## Frozen runtime

This artifact-contract Setup repair was developed from repository commit
`4434bfb1135f006b81dca4b6bb1285ff0a8216cb` with:

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
`--cd`, `--json`, and `--output-last-message`. The complete stdout byte stream
from `--json` is written directly to `codex_events.jsonl`; it is not embedded in
metadata or reconstructed from the final answer.

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
- E1 uses the complete ordered GT01–GT21 inventory in
  `skillnet_run_guide_v1_1/E1_scale_manifest.json`.
- Every E1 size-10 and size-30 A/B/C condition runs all 21 tasks. The six
  live conditions therefore create 126 new model calls.
- All tasks remain in scope when a smaller Catalogue omits a required Skill;
  the unchanged evaluator records the resulting route as a failure.
- A selects `A_flat_catalogue.json`.
- B selects `B_department_grouped_catalogue.json`.
- C selects `C_graph_structured_catalogue.json`; no separate relation file is
  read or passed.

Run output is stored at:

```text
experiments/skillnet/runs/<experiment>/<configuration>/size_<size>/<run_id>/
```

Artifact ownership is deterministic. The child only returns the fixed prediction
JSON. It never chooses paths or saves experiment files. `run_condition.py`
records the immutable inputs and transport outputs; `verify_condition.py` adds
the evaluator-derived artifacts after all responses exist.

After successful condition verification, every task directory contains:

1. `run_metadata.json`;
2. `packet_manifest.json` with the Chinese task input, isolation inventory, and
   input hashes;
3. `catalogue_snapshot.json` containing exactly the selected condition
   Catalogue at the JSON-value level;
4. `codex_events.jsonl`, the unmodified `codex exec --json` stdout bytes (empty
   only in fixture mode);
5. `raw_response.txt`, written through `--output-last-message` for live runs;
6. `prediction.json` only when direct parsing and canonical schema validation
   both succeed;
7. `schema_validation.json`;
8. `evaluation_trace.json`;
9. `graph_overlay.json`;
10. `result_row.json`, copied JSON-value-for-value from the deterministic
    evaluator's tidy per-task row.

`run_metadata.json` includes the experiment/task/condition identity, runtime
repository commit, Catalogue `source_commit`, CLI and model versions, start/end
timestamps, duration, exit code, exact command, stderr, and input hashes. A
missing last message is represented by an empty `raw_response.txt` plus
`raw_response_placeholder: true`; no model text is invented or repaired.

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

E1 size 46 is extracted from the corresponding formal E0 outputs and does not
start new model processes. Do not run E1 with `--size 46` during the formal
sequence and do not use `--resume`.

The formal all-21-task E0 sources are:

- A: `E0/A/size_46/run_02`;
- B: `E0/B/size_46/run_02`;
- C: `E0/C/size_46/run_04`.

The patched/non-formal B bundle, the failed C run, and infrastructure-failed
sources are excluded. Reuse metadata must retain the original configuration,
run ID, runtime commit, and artifact hashes.

## Deterministic verification

`verify_condition.py` ignores any saved `prediction.json` and mechanically
extracts the final JSON object again from each immutable `raw_response.txt`. It
does not correct fields, IDs, order, status, or meaning. Only extracted objects
that pass the canonical prediction schema and match their task ID are copied
into the dedicated evaluator predictions directory.

That predictions directory contains prediction JSON files only. Metadata,
validation records, commands, stdout, stderr, and evaluator results live
outside it.

The verifier writes `evaluation_trace.json`, `graph_overlay.json`, and
`result_row.json` back to the corresponding task directory with exclusive file
creation. The trace includes predicted/required/optional/missing/extra Skills,
department checks, hard-order, forbidden, conflict, mutex, final-status,
route-choice, blocked checks, and failure tags.

Graph overlays always use the same-size C Catalogue as their graph source. For
A/B, C is first opened only after every raw response is present and the
deterministic evaluator has returned; the overlay records
`post_evaluation_overlay: true` and `overlay_read_phase:
after_response_and_evaluator`. Thus A/B children never receive graph relations.
C overlays record `post_evaluation_overlay: false` because C was already the
run input.

At the end, `condition_validation.json` contains a per-task artifact matrix. Any
missing required artifact, or a `prediction.json` attached to an invalid schema
record, marks the condition `incomplete` and makes verification return nonzero.
This audit record and all existing task artifacts are never overwritten.

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
`experiments/skillnet/frozen_eval/E1_Gold_21_tasks.json`; it never silently
falls back to another Gold path.

## Frozen E1 Gold

The frozen 21-task files are:

```text
experiments/skillnet/frozen_eval/E1_Gold_21_tasks.json
experiments/skillnet/frozen_eval/E1_Gold_21_tasks_validation.json
```

They are mechanically generated with:

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py --prepare-e1-gold
```

The Gold file preserves all 21 canonical task records without modification at
the JSON-value level, retains the full evaluator metadata/catalogue fields,
sets `task_count` to 21, and records the full Gold hash, manifest hash, and
ordered manifest task IDs. The existing evaluator validates the resulting
package, and the validation report must contain `valid: true` and
`task_count: 21`.

## Fixture-only SETUP mode

`--fixture-response-dir <directory>` replaces `--execute` for setup tests. It
copies static `<task_id>.txt` responses and never starts Codex. Runs created in
this mode record `execution_mode: fixture` and must not be used as experimental
results. Fixture task directories contain a zero-byte `codex_events.jsonl` so
the same artifact inventory can be checked without pretending fixture events
were live CLI events.

Run it under a temporary `--state-root`, then run `verify_condition.py` against
the same temporary state. Do not place Setup output under the formal `runs/` or
`results/` trees.

## Synthetic live SETUP smoke test

Before formal execution, start exactly one fresh `codex exec` process with the
frozen CLI/model/reasoning flags, an empty temporary `--cd`, and a synthetic
prompt that contains neither a Gold task nor any Catalogue. Do not pass
`--output-schema`. Pass `--json`, save stdout byte-for-byte as
`codex_events.jsonl`, and use `--output-last-message` for `raw_response.txt`.
Require exit code zero, require every non-empty event line to parse as JSON, and
require a directly parseable final JSON object with exactly these keys:

```text
task_id, use_skills, selected_departments, skill_sequence,
final_status, blocked_by, route_choice, reason
```

The synthetic prompt must state the field types, including that `route_choice`
is a JSON object with string keys and values, and repeat the same three
status-consistency rules used by the runner. Validate all field types, those
rules, and the exact key set. A smoke output with an invalid field type or
inconsistent `use_skills`, `final_status`, or `blocked_by` value is a failed
Setup attempt even when transport and JSON parsing succeeded; preserve it and
use a new synthetic smoke ID after correcting the Setup instruction.

Transport reconnect messages are allowed provided they occur inside that same
process. Preserve the smoke command, `codex_events.jsonl`, stderr, raw response,
and validation result as Setup evidence; never treat the response as
experimental data.

## Setup test commands

Run the artifact contract independently, then the repository suite:

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python -m unittest discover -s experiments/skillnet/tests -v
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python -m unittest discover -s tests -v
```

The first command performs temporary E1 fixture runs only; it does not start
Codex and does not modify the formal `runs/` or `results/` trees. The synthetic
live smoke is a separate one-process Setup check and must not contain a Gold
task or Catalogue.
