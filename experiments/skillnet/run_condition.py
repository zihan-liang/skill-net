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
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RUN_REQUIRED_ARTIFACTS = (
    "run_metadata.json",
    "packet_manifest.json",
    "catalogue_snapshot.json",
    "codex_events.jsonl",
    "raw_response.txt",
    "schema_validation.json",
)


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_bytes(path: Path, value: bytes, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "xb" if exclusive else "wb"
    with path.open(mode) as handle:
        handle.write(value)


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
        canonical_task_ids = sorted(prompts, key=lambda item: int(item[2:4]))
        if task_ids != canonical_task_ids:
            raise ValueError(
                "E1 manifest task_ids must exactly equal the ordered canonical "
                "GT01-GT21 prompt inventory"
            )
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
- 只返回一个满足下方固定输出契约的 JSON 对象。
- 不要输出 Markdown、代码围栏、解释性前后缀或第二次答案。
- task_id 必须是 `{task_id}`。
- skill_sequence 和 blocked_by 只能使用当前 Catalogue 中的 canonical skill_id。
- selected_departments 只能使用当前 Catalogue 中的 canonical department_id。

固定输出契约（八个字段必须全部出现，不得增加其他字段）：
- task_id：字符串，值必须是 `{task_id}`。
- use_skills：布尔值。
- selected_departments：无重复字符串数组。
- skill_sequence：无重复字符串数组，按执行顺序排列。
- final_status：字符串，只能是 completed、blocked 或 no_tool。
- blocked_by：无重复字符串数组。
- route_choice：JSON 对象；每个键和值都必须是字符串。
- reason：非空字符串，简洁说明路由判断。

状态一致性规则：
- completed：use_skills 为 true，blocked_by 为空数组。
- blocked：use_skills 为 true，blocked_by 至少包含一个当前 Catalogue 的 canonical skill_id。
- no_tool：use_skills 为 false，selected_departments、skill_sequence、blocked_by 都为空数组。

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


def expected_run_artifacts(schema_validation: dict[str, Any]) -> list[str]:
    artifacts = list(RUN_REQUIRED_ARTIFACTS)
    if schema_validation.get("schema_valid") is True:
        artifacts.append("prediction.json")
    return artifacts


def build_packet_manifest(
    *,
    repo: Path,
    experiment: str,
    configuration: str,
    size: int,
    run_id: str,
    task_id: str,
    prompt_record: dict[str, str],
    child_prompt_sha256: str,
    catalogue_path: Path,
    catalogue_source_sha256: str,
    catalogue_embedded_sha256: str,
    catalogue_snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "experiment_id": experiment,
        "task_id": task_id,
        "configuration": configuration,
        "catalogue_size": size,
        "run_id": run_id,
        "delivery": {
            "child_prompt": "stdin",
            "raw_response": "codex --output-last-message",
            "cli_events": "codex --json stdout",
        },
        "child_working_directory": {
            "temporary": True,
            "contents_at_launch": [],
            "symlinks": [],
        },
        "child_visible_inputs": [
            "current_chinese_task",
            "selected_catalogue",
            "fixed_prediction_json_contract",
            "non_answer_metadata",
        ],
        "child_hidden_inputs": [
            "Gold",
            "deterministic_evaluator",
            "canonical_Skills",
            "other_tasks",
            "other_catalogues",
            "standalone_relations",
            "prior_results",
        ],
        "inputs": {
            "task_prompt": {
                "source": prompt_record["source"],
                "source_sha256": prompt_record["sha256"],
                "text_zh": prompt_record["prompt_zh"],
            },
            "catalogue": {
                "source": str(catalogue_path.relative_to(repo)),
                "source_sha256": catalogue_source_sha256,
                "embedded_json_sha256": catalogue_embedded_sha256,
                "snapshot_sha256": catalogue_snapshot_sha256,
            },
            "child_prompt": {
                "sha256": child_prompt_sha256,
                "assembled_by": str(Path(__file__).resolve().relative_to(repo)),
                "assembler_sha256": sha256_file(Path(__file__).resolve()),
            },
        },
    }


def execute_fixture(
    fixture_dir: Path,
    task_id: str,
    raw_path: Path,
    events_path: Path | None = None,
) -> tuple[int, str, str, bool]:
    if events_path is not None:
        write_bytes(events_path, b"", exclusive=True)
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
    *,
    events_path: Path | None = None,
) -> tuple[int, bytes, str, bool, list[str]]:
    if events_path is None:
        events_path = packet_dir / "codex_events.jsonl"
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
        "--json",
        "--cd",
        str(packet_dir),
        "--output-last-message",
        str(raw_path),
        "-",
    ]
    process = subprocess.run(
        command,
        input=prompt.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    stdout_bytes = (
        process.stdout.encode("utf-8")
        if isinstance(process.stdout, str)
        else process.stdout
    )
    stderr_text = (
        process.stderr
        if isinstance(process.stderr, str)
        else process.stderr.decode("utf-8", errors="replace")
    )
    write_bytes(events_path, stdout_bytes, exclusive=True)
    return (
        process.returncode,
        stdout_bytes,
        stderr_text,
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
    if args.experiment == "E1" and args.size == 46:
        raise SystemExit(
            "E1 size 46 reuses E0 and must not start run_condition child processes"
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
        condition_metadata = load_json(condition_metadata_path)
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
            if condition_metadata.get(key) != expected:
                raise SystemExit(
                    f"Resume identity mismatch for {key}: "
                    f"{condition_metadata.get(key)!r} != {expected!r}"
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
            "schema_version": "2.0",
            "experiment": args.experiment,
            "configuration": args.configuration,
            "size": args.size,
            "run_id": args.run_id,
            "task_ids": task_ids,
            "execution_mode": "codex" if args.execute else "fixture",
            "default_execution": "serial",
            "attempts_per_task": 1,
            "automatic_retries": 0,
            "transport_reconnects_allowed": True,
            "task_attempt_definition": "one fresh codex exec process",
            "created_at_utc": utc_now(),
            "repository_commit": git_head(repo),
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_source_commit": catalogue.get("source_commit"),
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
                "json_events": True,
                "output_last_message": True,
            },
            "python": {
                "executable": sys.executable,
                "version": sys.version.split()[0],
                "jsonschema_version": importlib.metadata.version("jsonschema"),
            },
        }
        write_json(condition_metadata_path, condition_metadata, exclusive=True)

    completed = 0
    skipped = 0
    child_failures = 0
    runner_missing_artifacts: dict[str, list[str]] = {}
    catalogue_source_sha256 = sha256_file(catalogue_path)
    catalogue_embedded_bytes = json.dumps(
        catalogue, ensure_ascii=False, indent=2
    ).encode("utf-8")
    schema_sha256 = sha256_file(schema_path)

    for task_id in task_ids:
        task_dir = run_root / task_id
        raw_path = task_dir / "raw_response.txt"
        events_path = task_dir / "codex_events.jsonl"
        prediction_path = task_dir / "prediction.json"
        validation_path = task_dir / "schema_validation.json"
        metadata_path = task_dir / "run_metadata.json"
        packet_manifest_path = task_dir / "packet_manifest.json"
        catalogue_snapshot_path = task_dir / "catalogue_snapshot.json"

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

        prompt = build_child_prompt(
            task_id, prompts[task_id]["prompt_zh"], catalogue
        )
        prompt_sha256 = sha256_bytes(prompt.encode("utf-8"))
        write_json(catalogue_snapshot_path, catalogue, exclusive=True)
        catalogue_snapshot_sha256 = sha256_file(catalogue_snapshot_path)
        packet_manifest = build_packet_manifest(
            repo=repo,
            experiment=args.experiment,
            configuration=args.configuration,
            size=args.size,
            run_id=args.run_id,
            task_id=task_id,
            prompt_record=prompts[task_id],
            child_prompt_sha256=prompt_sha256,
            catalogue_path=catalogue_path,
            catalogue_source_sha256=catalogue_source_sha256,
            catalogue_embedded_sha256=sha256_bytes(catalogue_embedded_bytes),
            catalogue_snapshot_sha256=catalogue_snapshot_sha256,
        )
        write_json(packet_manifest_path, packet_manifest, exclusive=True)

        started_datetime = datetime.now(timezone.utc)
        started_monotonic = time.monotonic()
        command: list[str] | None
        if args.fixture_response_dir:
            fixture_path = args.fixture_response_dir.resolve() / f"{task_id}.txt"
            command = ["fixture-copy", str(fixture_path), str(raw_path)]
            returncode, _stdout, stderr, raw_produced = execute_fixture(
                args.fixture_response_dir.resolve(),
                task_id,
                raw_path,
                events_path,
            )
        else:
            with tempfile.TemporaryDirectory(
                prefix=f"skillnet_{task_id}_"
            ) as packet:
                packet_dir = Path(packet)
                (
                    returncode,
                    _stdout,
                    stderr,
                    raw_produced,
                    command,
                ) = execute_codex(
                    PINNED_CODEX_PATH,
                    prompt,
                    raw_path.resolve(),
                    packet_dir,
                    events_path=events_path,
                )
        finished_monotonic = time.monotonic()
        finished_datetime = datetime.now(timezone.utc)

        if not events_path.exists():
            write_bytes(events_path, b"", exclusive=True)
        raw_response_placeholder = not raw_path.exists()
        if raw_response_placeholder:
            write_bytes(raw_path, b"", exclusive=True)

        validation, prediction = validate_direct_response(
            raw_path, canonical_schema, task_id
        )
        validation.update(
            {
                "raw_response_sha256": sha256_file(raw_path),
                "prediction_saved": prediction is not None,
            }
        )
        write_json(validation_path, validation, exclusive=True)
        if prediction is not None:
            write_json(prediction_path, prediction, exclusive=True)

        run_metadata = {
            "schema_version": "2.0",
            "experiment_id": args.experiment,
            "experiment": args.experiment,
            "task_id": task_id,
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "size": args.size,
            "run_id": args.run_id,
            "runtime_repo_commit": condition_metadata["repository_commit"],
            "catalogue_source_commit": catalogue.get("source_commit"),
            "codex_cli_version": condition_metadata["codex"]["version"],
            "model": PINNED_MODEL,
            "model_reasoning_effort": PINNED_REASONING_EFFORT,
            "start_time": started_datetime.isoformat(),
            "end_time": finished_datetime.isoformat(),
            "duration_seconds": round(
                finished_monotonic - started_monotonic, 6
            ),
            "exit_code": returncode,
            "input_hashes": {
                "prompt_source_sha256": prompts[task_id]["sha256"],
                "child_prompt_sha256": prompt_sha256,
                "catalogue_source_sha256": catalogue_source_sha256,
                "catalogue_embedded_json_sha256": sha256_bytes(
                    catalogue_embedded_bytes
                ),
                "catalogue_snapshot_sha256": catalogue_snapshot_sha256,
                "prediction_schema_sha256": schema_sha256,
                "runner_source_sha256": sha256_file(Path(__file__).resolve()),
            },
            "execution_mode": "codex" if args.execute else "fixture",
            "attempt_number": 1,
            "automatic_retry": False,
            "transport_reconnects_allowed": True,
            "task_attempt_definition": "one fresh codex exec process",
            "prompt_source": prompts[task_id]["source"],
            "catalogue_path": str(catalogue_path.relative_to(repo)),
            "catalogue_sha256": catalogue_source_sha256,
            "command": command,
            "stderr": stderr,
            "raw_response_produced": raw_produced,
            "raw_response_placeholder": raw_response_placeholder,
            "raw_response_sha256": sha256_file(raw_path),
            "codex_events_sha256": sha256_file(events_path),
            "prediction_saved": prediction is not None,
        }
        write_json(metadata_path, run_metadata, exclusive=True)

        missing = [
            filename
            for filename in expected_run_artifacts(validation)
            if not (task_dir / filename).is_file()
        ]
        if missing:
            runner_missing_artifacts[task_id] = missing
        if returncode != 0:
            child_failures += 1
        completed += 1

    summary = {
        "run_root": str(run_root),
        "task_count": len(task_ids),
        "task_artifact_sets_created": completed,
        "raw_responses_created": completed,
        "existing_raw_responses_skipped": skipped,
        "tasks_without_raw_response": 0,
        "child_process_failures": child_failures,
        "missing_run_artifacts": runner_missing_artifacts,
        "execution_mode": "codex" if args.execute else "fixture",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if runner_missing_artifacts:
        return 5
    return 0 if child_failures == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
