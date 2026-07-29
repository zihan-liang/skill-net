# Validation Report

## Validation baseline

- Authoritative branch inspected: `origin/main`
- Authoritative commit: `cdb4ecdf838fdd4e0bbb01e4c766b32eb430eb47`
- Working-package branch inspected: `codex/hr-skills`
- Working-package tip inspected: `62910cb97d6fb9e05b1895825106355724be3658`

## Results summary

| Check | Result |
|---|---|
| Canonical Skills match main | PASS — 46/46 |
| Canonical departments match main | PASS — 5/5 |
| All task IDs retained | PASS — 21/21 |
| Original Gold semantics preserved | PASS — every machine field compared task by task |
| Hard-order references valid | PASS |
| Blockers and task constraints valid | PASS |
| Completed/blocked/no-tool schema samples | PASS |
| Evaluator runs with Gold only | PASS |
| Gold-perfect end-to-end metrics | PASS — all success/precision/recall/F1/order/status/route/applicable accuracy metrics 1.0; constraint violation rate 0.0 |
| Valid alternative partial order | PASS |
| Invalid-input and routing failures | PASS |
| Chinese machine identifiers | PASS — none in validated machine fields |
| Legacy graph-evaluation tokens in operational files | PASS — none |
| Main repository tests | PASS — 142/142 |
| Bilingual package tests | PASS — 16/16 |
| CSV structure and render | PASS — 22 rows × 11 columns |

## Commands executed

### Refresh and inspect authoritative refs

```bash
git fetch origin main codex/hr-skills
git log -1 --format='%H %s' origin/main
git merge-base origin/main codex/hr-skills
git rev-list --left-right --count origin/main...codex/hr-skills
```

Result: latest main was `cdb4ecd`; merge-base was `bbc590d`; divergence was
47 main-only commits and 2 branch-only commits.

### Run all authoritative main tests

```bash
python3 -m unittest discover -s tests -v
```

Run from a detached local worktree at authoritative main.

Result: `Ran 142 tests ... OK`.

### Validate the bilingual Gold package

```bash
python3 evaluation/evaluate_skillnet.py validate-package \
  --gold 02_Gold_Standard_21_V4.json \
  --output results/package_validation_report.json
```

Result:

```json
{
  "valid": true,
  "task_count": 21,
  "skill_count": 46,
  "errors": [],
  "warnings": []
}
```

### Run bilingual regression tests

```bash
SKILLNET_MAIN_ROOT=/tmp/skillnet_main_cdb4ecd_20260729 \
SKILLNET_ORIGINAL_PACKAGE=/Users/xrx/Desktop/SJTU_Summer_School/skill-net/SkillNet_Gold_Tasks_V4 \
PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover -s evaluation/tests -v
```

Result: `Ran 16 tests ... OK`.

Coverage includes:

- exact mapping to main Skill IDs, `SKILL.md` frontmatter, and H1 titles;
- exact department IDs from main;
- preservation of all original Gold machine semantics;
- complete English and Chinese text for all 21 tasks;
- schema acceptance for completed, blocked, and no-tool outputs;
- schema rejection of an unknown Skill;
- Gold-perfect 100% metrics;
- acceptance of an alternative valid partial order;
- detection of invalid JSON, unknown Skill, missing required Skill, order
  violation, blocked-flow continuation, and false tool activation.

### End-to-end CLI evaluation

```bash
python3 evaluation/evaluate_skillnet.py evaluate \
  --gold 02_Gold_Standard_21_V4.json \
  --predictions evaluation/fixtures/gold_perfect_predictions.jsonl \
  --configuration VALIDATION \
  --run-id 1 \
  --output-dir /tmp/skillnet_bilingual_cli_validation_20260729/perfect
```

Result: 21 tasks evaluated; zero unmatched or duplicate records.

The summary reported:

- Functional Success: 1.0
- Clean Success: 1.0
- Skill Precision/Recall/F1: 1.0 / 1.0 / 1.0
- Department Precision/Recall/F1: 1.0 / 1.0 / 1.0
- Required Order Accuracy: 1.0
- Final Status Accuracy: 1.0
- Route Choice Accuracy: 1.0
- No-Tool Accuracy: 1.0
- Blocked-Flow Accuracy: 1.0
- Gold Constraint Violation Rate: 0.0

### Aggregate CLI output

```bash
python3 evaluation/evaluate_skillnet.py aggregate \
  --input-root /tmp/skillnet_bilingual_cli_validation_20260729 \
  --output-dir /tmp/skillnet_bilingual_cli_validation_20260729/aggregate
```

Result: one result file and 21 rows aggregated; aggregate metrics matched the
single-run 100%/0% results above.

### CSV validation

```bash
/Users/xrx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node \
  /tmp/skillnet_csv_artifact_20260729/verify_coverage_csv.mjs
```

The bundled spreadsheet runtime imported the CSV as a worksheet, inspected
`A1:K22`, rendered it, and exported a verification workbook.

Result: 22 rows including the header, 11 columns, all 21 task IDs present, English
headers present, Chinese display columns readable, and no structural error.

### Static checks

```bash
python3 -m py_compile evaluation/evaluate_skillnet.py
python3 -m json.tool 02_Gold_Standard_21_V4.json
python3 -m json.tool skill_name_map.json
```

Additional structured scans checked every machine Skill and department position,
all JSONL records, duplicate IDs, missing English text, stale graph-evaluation
tokens, and noncanonical Chinese machine identifiers.

Result: PASS.

### ZIP integrity and extracted-package validation

```bash
unzip -t SkillNet_Gold_Tasks_V4_English_Bilingual.zip
unzip -q SkillNet_Gold_Tasks_V4_English_Bilingual.zip \
  -d /tmp/skillnet_zip_verify_20260729

PYTHONDONTWRITEBYTECODE=1 \
SKILLNET_MAIN_ROOT=/tmp/skillnet_main_cdb4ecd_20260729 \
SKILLNET_ORIGINAL_PACKAGE=/Users/xrx/Desktop/SJTU_Summer_School/skill-net/SkillNet_Gold_Tasks_V4 \
python3 -m unittest discover \
  -s /tmp/skillnet_zip_verify_20260729/SkillNet_Gold_Tasks_V4_English_Bilingual/evaluation/tests \
  -v
```

Result: compressed-data integrity passed for every entry; the extracted package
again passed all 16 regression tests and package validation with 21 tasks,
46 Skills, zero errors, and zero warnings.

## Remaining limitations

- Main defines exact Skill IDs and `SKILL.md` English titles, but it does not
  define separate English or Chinese department display titles. Department IDs
  are authoritative; display labels are documented compatibility labels.
- Some `agents/openai.yaml` interface titles differ in capitalization or wording
  from the `SKILL.md` H1. `name_en` consistently uses the H1; every discrepancy is
  listed in `SKILL_NAME_MAPPING_REPORT.md`.
- English task text is a faithful bilingual rendering of the approved Chinese
  tasks, not a separate upstream task specification. The semantic-preservation
  test verifies all machine Gold fields against the original package.
- `predictions_template.jsonl` intentionally contains placeholders and is not a
  valid submission until those placeholders are filled.
