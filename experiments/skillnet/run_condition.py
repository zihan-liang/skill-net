#!/usr/bin/env python3
"""Run one frozen SkillNet E0/E1 condition.

Each task is sent to a fresh, ephemeral ``codex exec`` process. The child
process receives only the current Chinese task, the one selected Catalogue,
and a fixed JSON output contract. Gold data and evaluator files are never
included in the child packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PINNED_CODEX_PATH = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
PINNED_CODEX_VERSION = "codex-cli 0.146.0-alpha.3.1"
PINNED_MODEL = "gpt-5.6-sol"
PINNED_REASONING_EFFORT = "high"

CONFIGURATION_FILENAMES = {
    "A": "A_flat_catalogue.json",
    "B": "B_department_grouped_catalogue.json",
    "C": "C_graph_structured_catalogue.json",
}
REQUIRED_PREDICTION_FIELDS = (
    "task_id",
    "use_skills",
    "selected_departments",
    "skill_sequence",
    "final_status",
    "blocked_by",
    "route_choice",
    "reason",
)
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# This fixed shape is passed to every child via --output-schema. It deliberately
# contains no Skill or department enum, so a small Catalogue does not leak IDs
# from a larger condition. The canonical repository schema is applied after the
# response is produced.
CHILD_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": list(REQUIRED_PREDICTION_FIELDS),
    "properties": {
        "task_id": {"type": "string", "pattern": "^GT[0-9]{2}_[A-Z0-9_]+$"},
        "use_skills": {"type": "boolean"},
        "selected_departments": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "skill_sequence": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "final_status": {"enum": ["completed", "blocked", "no_tool"]},
        "blocked_by": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "route_choice": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "reason": {"type": "string", "minLength": 1},
    },
    "allOf": [
        {
            "if": {"properties": {"final_status": {"const": "no_tool"}}},
            "then": {
                "properties": {
                    "use_skills": {"const": False},
                    "selected_departments": {"maxItems": 0},
                    "skill_sequence": {"maxItems": 0},
                    "blocked_by": {"maxItems": 0},
                }
            },
        },
        {
            "if": {"properties": {"final_status": {"const": "blocked"}}},
            "then": {
                "properties": {
                    "use_skills": {"const": True},
                    "blocked_by": {"minItems": 1},
                }
            },
        },
        {
            "if": {"properties": {"final_status": {"const": "completed"}}},
            "then": {
                "properties": {
                    "use_skills": {"const": True},
                    "blocked_by": {"maxItems": 0},
                }
            },
        },
    ],
    "additionalProperties": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def git_head(repo: Path) -> str:
    process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return process.stdout.strip()


def codex_version(codex_bin: Path) -> str:
    process = subprocess.run(
        [str(codex_bin), "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    lines = [line.strip() for line in process.stdout.splitlines() if line.strip()]
    version = next((line for line in lines if line.startswith("codex-cli ")), "")
    if process.returncode != 0 or not version:
        raise RuntimeError(
            f"Unable to read Codex CLI version from {codex_bin}: "
            f"{process.stderr.strip()}"
        )
    return version


def extract_chinese_prompt(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    first_line = text.splitlines()[0] if text else ""
    if not first_line.startswith("Task ID: "):
        raise ValueError(f"Missing Task ID header: {path}")
    task_id = first_line.removeprefix("Task ID: ").strip()
    marker = "\n中文任务\n"
    end_marker = "\n\nOutput requirements"
    if marker not in text or end_marker not in text:
        raise ValueError(f"Cannot isolate Chinese prompt: {path}")
    prompt_zh = text.split(marker, 1)[1].split(end_marker, 1)[0].strip()
    if not prompt_zh:
        raise ValueError(f"Empty Chinese prompt: {path}")
    return task_id, prompt_zh


def load_prompt_map(repo: Path) -> dict[str, dict[str, str]]:
    prompt_dir = repo / "SkillNet_Gold_Tasks_V4" / "prompts"
    records: dict[str, dict[str, str]] = {}
    for path in sorted(prompt_dir.glob("GT*.txt")):
        task_id, prompt_zh = extract_chinese_prompt(path)
        if task_id in records:
            raise ValueError(f"Duplicate prompt task_id: {task_id}")
        records[task_id] = {
            "prompt_zh": prompt_zh,
            "source": str(path.relative_to(repo)),
            "sha256": sha256_file(path),
        }
    expected_numbers = list(range(1, 22))
    actual_numbers = sorted(int(task_id[2:4]) for task_id in records)
    if len(records) != 21 or actual_numbers != expected_numbers:
        raise ValueError(
            f"Expected GT01-GT21 exactly once; found {sorted(records)}"
        )
    return records


def flatten_catalogue_skills(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    if catalogue.get("configuration") == "A":
        skills = catalogue.get("skills", [])
    else:
        skills = [
            skill
            for department in catalogue.get("departments", [])
            for skill in department.get("skills", [])
        ]
    if not all(isinstance(item, dict) for item in skills):
        raise ValueError("Catalogue skills must be JSON objects")
    return skills


def resolve_condition(
    repo: Path,
    experiment: str,
    configuration: str,
    size: int,
) -> tuple[Path, dict[str, Any], list[str]]:
    if experiment == "E0" and size != 46:
        raise ValueError("E0 is fixed to size 46")
    if experiment == "E1" and size not in {10, 30, 46}:
        raise ValueError("E1 size must be 10, 30, or 46")

    catalogue_path = (
        repo
        / "skillnet_run_guide_v1_1"
        / "catalogues"
        / f"size_{size}"
        / CONFIGURATION_FILENAMES[configuration]
    )
    catalogue = load_json(catalogue_path)
    if catalogue.get("configuration") != configuration:
        raise ValueError(f"Catalogue configuration mismatch: {catalogue_path}")
    if catalogue.get("catalogue_size") != size:
        raise ValueError(f"Catalogue size mismatch: {catalogue_path}")
    skill_ids = [item.get("skill_id") for item in flatten_catalogue_skills(catalogue)]
    if len(skill_ids) != size or len(set(skill_ids)) != size:
        raise ValueError(f"Catalogue has wrong or duplicate Skill IDs: {catalogue_path}")

    prompts = load_prompt_map(repo)
    if experiment == "E0":
        task_ids = sorted(prompts, key=lambda item: int(item[2:4]))
    else:
        manifest_path = repo / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json"
        manifest = load_json(manifest_path)
        task_ids = manifest.get("task_ids", [])
        if not isinstance(task_ids, list) or len(task_ids) != 5:
            raise ValueError("E1 manifest must contain exactly five task_ids")
        if any(task_id not in prompts for task_id in task_ids):
            raise ValueError("E1 manifest references a missing prompt")
    return catalogue_path, catalogue, task_ids


def canonical_schema_path(repo: Path) -> Path:
    return (
        repo
        / "SkillNet_Gold_Tasks_V4"
        / "evaluation"
        / "prediction_schema.json"
    )


def schema_errors(
    prediction: Any,
    schema: dict[str, Any],
    expected_task_id: str,
) -> list[dict[str, str]]:
    errors = [
        {
            "path": ".".join(str(part) for part in error.absolute_path),
            "message": error.message,
        }
        for error in sorted(
            Draft202012Validator(schema).iter_errors(prediction),
            key=lambda item: list(item.absolute_path),
        )
    ]
    if isinstance(prediction, dict) and prediction.get("task_id") != expected_task_id:
        errors.append(
            {
                "path": "task_id",
                "message": (
                    f"task_id must equal {expected_task_id!r}; "
                    f"received {prediction.get('task_id')!r}"
                ),
            }
        )
    return errors


def validate_direct_response(
    raw_path: Path,
    schema: dict[str, Any],
    expected_task_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    report: dict[str, Any] = {
        "task_id": expected_task_id,
        "raw_response_exists": raw_path.is_file(),
        "direct_json_parse": False,
        "schema_valid": False,
        "task_id_match": False,
        "errors": [],
    }
    if not raw_path.is_file():
        report["errors"].append(
            {"path": "", "message": "raw_response.txt was not produced"}
        )
        return report, None
    raw = raw_path.read_text(encoding="utf-8")
    try:
        prediction = json.loads(raw)
        report["direct_json_parse"] = True
    except json.JSONDecodeError as exc:
        report["errors"].append(
            {
                "path": "",
                "message": f"raw response is not directly parseable JSON: {exc}",
            }
        )
        return report, None
    if not isinstance(prediction, dict):
        report["errors"].append(
            {"path": "", "message": "prediction must be a JSON object"}
        )
        return report, None
    errors = schema_errors(prediction, schema, expected_task_id)
    report["errors"] = errors
    report["task_id_match"] = prediction.get("task_id") == expected_task_id
    report["schema_valid"] = not errors
    return report, prediction if not errors else None


def build_child_prompt(
    task_id: str,
    prompt_zh: str,
    catalogue: dict[str, Any],
) -> str:
    catalogue_text = json.dumps(catalogue, ensure_ascii=False, indent=2)
    return f"""你正在完成一个隔离的 SkillNet 路由任务。

严格限制：
- 不要调用任何工具，不要读取文件，不要检查仓库或外部信息。
- 只能使用下方“当前中文任务”和“当前唯一 Catalogue”。
- 不得假设或使用 Catalogue 之外的 Skill。
- 只进行路由预测，不执行任何业务动作。
- 只返回一个满足固定输出 schema 的 JSON 对象。
- 不要输出 Markdown、代码围栏、解释性前后缀或第二次答案。
- task_id 必须是 `{task_id}`。
- skill_sequence 和 blocked_by 只能使用当前 Catalogue 中的 canonical skill_id。
- selected_departments 只能使用当前 Catalogue 中的 canonical department_id。

当前中文任务：
{prompt_zh}

当前唯一 Catalogue：
{catalogue_text}
"""


def condition_run_root(
    state_root: Path,
    experiment: str,
    configuration: str,
    size: int,
    run_id: str,
) -> Path:
    return (
        state_root
        / "runs"
        / experiment
        / configuration
        / f"size_{size}"
        / run_id
    )


def execute_fixture(
    fixture_dir: Path,
    task_id: str,
    raw_path: Path,
) -> tuple[int, str, str, bool]:
    fixture_path = fixture_dir / f"{task_id}.txt"
    if not fixture_path.is_file():
        return 4, "", f"Missing fixture response: {fixture_path}", False
    shutil.copyfile(fixture_path, raw_path)
    return 0, "", "", True


def execute_codex(
    codex_bin: Path,
    prompt: str,
    raw_path: Path,
    packet_dir: Path,
) -> tuple[int, str, str, bool, list[str]]:
    output_schema_path = packet_dir / "output_schema.json"
    write_json(output_schema_path, CHILD_OUTPUT_SCHEMA, exclusive=True)
    command = [
        str(codex_bin),
        "exec",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--model",
        PINNED_MODEL,
        "-c",
        f'model_reasoning_effort="{PINNED_REASONING_EFFORT}"',
        "--color",
        "never",
        "--output-schema",
        str(output_schema_path),
        "--cd",
        str(packet_dir),
        "--output-last-message",
        str(raw_path),
        "-",
    ]
    process = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    return (
        process.returncode,
        process.stdout,
        process.stderr,
        raw_path.is_file(),
        command,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", choices=("E0", "E1"), required=True)
    parser.add_argument("--configuration", choices=("A", "B", "C"), required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Run real, one-shot Codex child processes.",
    )
    mode.add_argument(
        "--fixture-response-dir",
        type=Path,
        help="SETUP testing only: use static raw responses instead of Codex.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Only fill tasks that do not already have raw_response.txt.",
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not RUN_ID_PATTERN.fullmatch(args.run_id):
        raise SystemExit(
            "run_id must match [A-Za-z0-9][A-Za-z0-9._-]*"
        )

    repo = repository_root()
    state_root = args.state_root.resolve()
    catalogue_path, catalogue, task_ids = resolve_condition(
        repo, args.experiment, args.configuration, args.size
    )
    prompts = load_prompt_map(repo)
    schema_path = canonical_schema_path(repo)
    canonical_schema = load_json(schema_path)
    run_root = condition_run_root(
        state_root,
        args.experiment,
        args.configuration,
        args.size,
        args.run_id,
    )
    condition_metadata_path = run_root / "condition_metadata.json"

    if args.resume:
        if not run_root.is_dir() or not condition_metadata_path.is_file():
            raise SystemExit(f"Cannot resume missing run: {run_root}")
        existing = load_json(condition_metadata_path)
        identity = {
            "experiment": args.experiment,
            "configuration": args.configuration,
            "size": args.size,
            "run_id": args.run_id,
            "task_ids": task_ids,
            "catalogue_sha256": sha256_file(catalogue_path),
            "execution_mode": "codex" if args.execute else "fixture",
        }
        for key, expected in identity.items():
            if existing.get(key) != expected:
                raise SystemExit(
                    f"Resume identity mismatch for {key}: "
                    f"{existing.get(key)!r} != {expected!r}"
                )
    else:
        if run_root.exists():
            raise SystemExit(
                f"Run already exists and will not be overwritten: {run_root}"
            )
        cli_version = (
            codex_version(PINNED_CODEX_PATH)
            if args.execute
            else PINNED_CODEX_VERSION
        )
        if args.execute and cli_version != PINNED_CODEX_VERSION:
            raise SystemExit(
                f"Codex CLI version drift: expected {PINNED_CODEX_VERSION!r}, "
                f"found {cli_version!r}"
            )
        run_root.mkdir(parents=True)
        condition_metadata = {
            "schema_version": "1.0",
            "experiment": args.experiment,
            "configuration": args.configuration,
            "size": args.size,
            "run_id": args.run_id,
            "task_ids": task_ids,
            "execution_mode": "codex" if args.execute else "fixture",
            "default_execution": "serial",
            "attempts_per_task": 1,
            "automatic_retries": 0,
            "created_at_utc": utc_now(),
            "repository_commit": git_head(repo),
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_sha256": sha256_file(catalogue_path),
            "prediction_schema_path": str(schema_path.relative_to(repo)),
            "prediction_schema_sha256": sha256_file(schema_path),
            "e1_manifest_sha256": (
                sha256_file(
                    repo / "skillnet_run_guide_v1_1" / "E1_scale_manifest.json"
                )
                if args.experiment == "E1"
                else None
            ),
            "codex": {
                "path": str(PINNED_CODEX_PATH),
                "version": cli_version,
                "model": PINNED_MODEL,
                "model_reasoning_effort": PINNED_REASONING_EFFORT,
                "user_config_ignored": True,
                "ephemeral": True,
                "sandbox": "read-only",
            },
        }
        write_json(condition_metadata_path, condition_metadata, exclusive=True)

    completed = 0
    skipped = 0
    no_raw_response = 0
    for task_id in task_ids:
        task_dir = run_root / task_id
        raw_path = task_dir / "raw_response.txt"
        prediction_path = task_dir / "prediction.json"
        validation_path = task_dir / "schema_validation.json"
        metadata_path = task_dir / "run_metadata.json"

        if raw_path.exists():
            if args.resume:
                skipped += 1
                continue
            raise SystemExit(
                f"Refusing to overwrite existing raw response: {raw_path}"
            )
        if prediction_path.exists():
            raise SystemExit(
                f"Inconsistent run: prediction exists without raw response: "
                f"{prediction_path}"
            )
        task_dir.mkdir(parents=True, exist_ok=True)

        started_at = utc_now()
        prompt = build_child_prompt(
            task_id, prompts[task_id]["prompt_zh"], catalogue
        )
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        command: list[str] | None = None
        if args.fixture_response_dir:
            returncode, stdout, stderr, raw_produced = execute_fixture(
                args.fixture_response_dir.resolve(), task_id, raw_path
            )
        else:
            with tempfile.TemporaryDirectory(
                prefix=f"skillnet_{task_id}_"
            ) as packet:
                packet_dir = Path(packet)
                (
                    returncode,
                    stdout,
                    stderr,
                    raw_produced,
                    command,
                ) = execute_codex(
                    PINNED_CODEX_PATH,
                    prompt,
                    raw_path.resolve(),
                    packet_dir,
                )
        finished_at = utc_now()

        validation, prediction = validate_direct_response(
            raw_path, canonical_schema, task_id
        )
        write_json(validation_path, validation)
        if prediction is not None:
            write_json(prediction_path, prediction, exclusive=True)

        run_metadata = {
            "schema_version": "1.0",
            "experiment": args.experiment,
            "configuration": args.configuration,
            "size": args.size,
            "run_id": args.run_id,
            "task_id": task_id,
            "execution_mode": "codex" if args.execute else "fixture",
            "attempt_number": 1,
            "automatic_retry": False,
            "started_at_utc": started_at,
            "finished_at_utc": finished_at,
            "prompt_source": prompts[task_id]["source"],
            "prompt_source_sha256": prompts[task_id]["sha256"],
            "child_prompt_sha256": prompt_sha256,
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_sha256": sha256_file(catalogue_path),
            "codex_cli_version": PINNED_CODEX_VERSION,
            "model": PINNED_MODEL,
            "model_reasoning_effort": PINNED_REASONING_EFFORT,
            "command": command,
            "exit_code": returncode,
            "raw_response_produced": raw_produced,
            "stdout": stdout,
            "stderr": stderr,
            "prediction_saved": prediction is not None,
        }
        write_json(metadata_path, run_metadata)
        if raw_produced:
            completed += 1
        else:
            no_raw_response += 1

    summary = {
        "run_root": str(run_root),
        "task_count": len(task_ids),
        "raw_responses_created": completed,
        "existing_raw_responses_skipped": skipped,
        "tasks_without_raw_response": no_raw_response,
        "execution_mode": "codex" if args.execute else "fixture",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if no_raw_response == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
