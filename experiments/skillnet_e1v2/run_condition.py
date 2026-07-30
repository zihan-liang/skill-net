#!/usr/bin/env python3
"""Run one isolated SkillNet E1-v2 task-conditioned size/configuration.

The default path is fixture-only Setup validation. ``--execute`` exists for a
later human-approved formal phase, but this Setup module never calls it.
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


EXPERIMENT_ID = "E1V2"
PINNED_CODEX_PATH = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
PINNED_CODEX_VERSION = "codex-cli 0.146.0-alpha.3.1"
PINNED_MODEL = "gpt-5.6-sol"
PINNED_REASONING_EFFORT = "high"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
CONFIGURATION_FILENAMES = {
    "A": "A_flat_catalogue.json",
    "B": "B_department_grouped_catalogue.json",
    "C": "C_graph_structured_catalogue.json",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any, *, exclusive: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_bytes(path: Path, value: bytes, *, exclusive: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb" if exclusive else "wb") as handle:
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


def codex_version(path: Path) -> str:
    process = subprocess.run(
        [str(path), "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    version = next(
        (
            line.strip()
            for line in process.stdout.splitlines()
            if line.strip().startswith("codex-cli ")
        ),
        "",
    )
    if process.returncode or not version:
        raise RuntimeError(f"Cannot read Codex CLI version: {process.stderr}")
    return version


def gold_path(repo: Path) -> Path:
    return (
        repo
        / "SkillNet_Gold_Tasks_V4"
        / "e1v2"
        / "E1V2_Gold_21.json"
    )


def schema_path(repo: Path) -> Path:
    return (
        repo
        / "experiments"
        / "skillnet_e1v2"
        / "prediction_schema_e1v2.json"
    )


def pool_manifest_path(repo: Path) -> Path:
    return (
        repo
        / "skillnet_run_guide_v1_1"
        / "e1v2_catalogues"
        / "candidate_pool_manifest.json"
    )


def task_catalogue_path(
    repo: Path, task_id: str, size: int, configuration: str
) -> Path:
    return (
        repo
        / "skillnet_run_guide_v1_1"
        / "e1v2_catalogues"
        / "tasks"
        / task_id
        / f"size_{size}"
        / CONFIGURATION_FILENAMES[configuration]
    )


def load_condition(
    repo: Path, configuration: str, size: int
) -> tuple[dict[str, Any], list[str], dict[str, dict[str, Any]]]:
    if size not in {10, 30, 46}:
        raise ValueError("E1V2 size must be 10, 30, or 46")
    gold = load_json(gold_path(repo))
    manifest = load_json(pool_manifest_path(repo))
    task_ids = [task["task_id"] for task in gold["tasks"]]
    manifest_ids = [record["task_id"] for record in manifest["tasks"]]
    if (
        gold.get("experiment_id") != EXPERIMENT_ID
        or len(task_ids) != 21
        or len(set(task_ids)) != 21
        or task_ids != manifest_ids
    ):
        raise ValueError("Frozen E1V2 Gold/manifest identity mismatch")
    tasks = {task["task_id"]: task for task in gold["tasks"]}
    for task_id in task_ids:
        catalogue = load_json(
            task_catalogue_path(repo, task_id, size, configuration)
        )
        if (
            catalogue.get("experiment_id") != EXPERIMENT_ID
            or catalogue.get("task_id") != task_id
            or catalogue.get("catalogue_size") != size
            or catalogue.get("configuration") != configuration
        ):
            raise ValueError(f"Catalogue identity mismatch for {task_id}")
    return gold, task_ids, tasks


def build_child_prompt(
    task_id: str,
    prompt_zh: str,
    catalogue: dict[str, Any],
) -> str:
    catalogue_text = json.dumps(catalogue, ensure_ascii=False, indent=2)
    return f"""你正在完成一个隔离的 SkillNet E1-v2 路由任务。

严格限制：
- 不要调用任何工具，不要读取文件，不要检查仓库或外部信息。
- 只能使用下方“当前中文任务”和“当前唯一 Catalogue”。
- 不得假设或使用 Catalogue 之外的 Skill。
- 只生成路由计划，不执行任何现实业务动作。
- 只返回一个 JSON 对象；不得输出 Markdown、代码围栏、前后缀或第二次答案。

固定八字段输出契约（必须全部出现，不得增加或删除字段）：
- task_id：字符串，必须是 `{task_id}`。
- use_skills：布尔值。
- selected_departments：无重复 canonical department_id 字符串数组。
- skill_sequence：无重复 canonical skill_id 字符串数组。
- final_status：只能是 completed、blocked 或 no_tool。
- blocked_by：无重复 canonical skill_id 字符串数组。
- route_choice：JSON 对象；键和值都必须是字符串。
- reason：非空字符串。

route_choice 固定表达：
- 当前任务没有分支选择：{{}}
- 验收路线只能是 {{"acceptance_route":"technical_acceptance"}} 或 {{"acceptance_route":"business_acceptance"}}
- 自研或外购路线只能是 {{"build_or_buy":"internal_development"}} 或 {{"build_or_buy":"external_procurement"}}
- 不得使用 `delivery_mode`。
- 不得使用 `development_mode`。
- 不得使用 `single_primary_acceptance_route`。
- 不得使用 `build`。
- 不得使用 `internal_build`。
- 不得使用 `technology-test-acceptance` 作为 route_choice 值。
- 不得使用 `business-acceptance` 作为 route_choice 值。
- 不得使用 `business_acceptance_route`。

final_status 语义：
- completed：已经成功生成完整 Skill 路由计划；不表示现实业务步骤已执行完毕。
- blocked：题目明确给出失败、不合格、拒绝或失败门禁，导致下游路线不能继续。
- no_tool：当前任务不需要任何 Skill。
- 仅仅因为路线中还有未来步骤尚未完成，不等于 blocked。

skill_sequence 语义：
- 只包含接下来真实应该执行的 Skills，并按实际执行顺序排列。
- 不包含已经完成的 Skills。
- 不包含已经产生失败结果的门禁 Skill。
- 不包含被阻断、不得执行的下游 Skills。
- final_status=blocked 时，skill_sequence 必须为空数组。
- final_status=no_tool 时，skill_sequence 必须为空数组。

blocked_by 语义：
- 只填写造成阻断的上游 Skill。
- 不填写被阻止执行的下游 Skills。
- final_status=blocked 时至少包含一个当前 Catalogue 的 canonical skill_id。
- final_status 不是 blocked 时必须为空数组。

no_tool 一致性：
- use_skills=false 时，final_status 必须为 no_tool。
- selected_departments、skill_sequence、blocked_by 必须都是空数组。
- route_choice 必须是 {{}}。

当前中文任务：
{prompt_zh}

当前唯一 Catalogue：
{catalogue_text}
"""


def schema_errors(
    prediction: Any,
    schema: dict[str, Any],
    expected_task_id: str,
) -> list[dict[str, str]]:
    errors = [
        {
            "path": ".".join(str(item) for item in error.absolute_path),
            "message": error.message,
        }
        for error in Draft202012Validator(schema).iter_errors(prediction)
    ]
    if isinstance(prediction, dict) and prediction.get("task_id") != expected_task_id:
        errors.append(
            {
                "path": "task_id",
                "message": f"task_id must equal {expected_task_id!r}",
            }
        )
    return errors


def validate_raw(
    raw_path: Path,
    schema: dict[str, Any],
    task_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    report = {
        "task_id": task_id,
        "raw_response_exists": raw_path.is_file(),
        "raw_response_nonempty": False,
        "direct_json_parse": False,
        "schema_valid": False,
        "task_id_match": False,
        "errors": [],
    }
    if not raw_path.is_file():
        report["errors"].append(
            {"path": "", "message": "raw_response.txt missing"}
        )
        return report, None
    raw = raw_path.read_text(encoding="utf-8")
    report["raw_response_nonempty"] = bool(raw.strip())
    if not raw.strip():
        report["errors"].append({"path": "", "message": "empty response"})
        return report, None
    try:
        prediction = json.loads(raw)
        report["direct_json_parse"] = True
    except json.JSONDecodeError as exc:
        report["errors"].append(
            {"path": "", "message": f"invalid JSON: {exc}"}
        )
        return report, None
    errors = schema_errors(prediction, schema, task_id)
    report["errors"] = errors
    report["task_id_match"] = (
        isinstance(prediction, dict)
        and prediction.get("task_id") == task_id
    )
    report["schema_valid"] = not errors
    return report, prediction if not errors else None


def run_root(
    state_root: Path,
    configuration: str,
    size: int,
    run_id: str,
) -> Path:
    return (
        state_root
        / "runs"
        / EXPERIMENT_ID
        / configuration
        / f"size_{size}"
        / run_id
    )


def execute_codex(
    prompt: str,
    raw_path: Path,
    events_path: Path,
    packet_dir: Path,
) -> tuple[int, str, list[str], int, str | None, str | None]:
    command = [
        str(PINNED_CODEX_PATH),
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
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(
        input=prompt.encode("utf-8"),
    )
    write_bytes(events_path, stdout)
    thread_id = codex_thread_id_from_events(stdout)
    missing_reason = None
    if thread_id is None:
        missing_reason = (
            "codex_process_failed_before_thread_started"
            if process.returncode != 0
            else "codex_process_completed_without_thread_started"
        )
    return (
        process.returncode,
        stderr.decode("utf-8", errors="replace"),
        command,
        process.pid,
        thread_id,
        missing_reason,
    )


def codex_thread_id_from_events(events: bytes) -> str | None:
    """Extract the first valid thread.started ID from one task's raw events."""
    for raw_line in events.splitlines():
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if event.get("type") != "thread.started":
            continue
        thread_id = event.get("thread_id")
        if isinstance(thread_id, str) and thread_id.strip():
            return thread_id
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", choices=("A", "B", "C"), required=True)
    parser.add_argument("--size", type=int, choices=(10, 30, 46), required=True)
    parser.add_argument("--run-id", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--fixture-response-dir", type=Path)
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
        raise SystemExit("Invalid run_id")
    repo = repository_root()
    state_root = args.state_root.resolve()
    gold, task_ids, tasks = load_condition(repo, args.configuration, args.size)
    schema_file = schema_path(repo)
    schema = load_json(schema_file)
    condition_root = run_root(
        state_root, args.configuration, args.size, args.run_id
    )
    if condition_root.exists():
        raise SystemExit(f"Run exists and will not be overwritten: {condition_root}")
    cli_version = (
        codex_version(PINNED_CODEX_PATH)
        if args.execute
        else PINNED_CODEX_VERSION
    )
    if args.execute and cli_version != PINNED_CODEX_VERSION:
        raise SystemExit(
            f"Codex version drift: {cli_version!r} != {PINNED_CODEX_VERSION!r}"
        )
    condition_root.mkdir(parents=True)
    condition_metadata = {
        "schema_version": "E1V2-1.0",
        "experiment_id": EXPERIMENT_ID,
        "configuration": args.configuration,
        "size": args.size,
        "run_id": args.run_id,
        "task_ids": task_ids,
        "task_count": len(task_ids),
        "execution_mode": "codex" if args.execute else "fixture",
        "formal_model_task": bool(args.execute),
        "execution_order": "serial",
        "max_workers": 1,
        "attempts_per_task": 1,
        "automatic_retries": 0,
        "resume_used": False,
        "created_at_utc": utc_now(),
        "repository_commit": git_head(repo),
        "gold_path": str(gold_path(repo).relative_to(repo)),
        "gold_sha256": sha256_file(gold_path(repo)),
        "pool_manifest_sha256": sha256_file(pool_manifest_path(repo)),
        "prediction_schema_sha256": sha256_file(schema_file),
        "semantic_normalization_sha256": sha256_file(
            Path(__file__).resolve().parent / "semantic_normalization.json"
        ),
        "runtime": {
            "codex_path": str(PINNED_CODEX_PATH),
            "codex_version": cli_version,
            "model": PINNED_MODEL,
            "model_reasoning_effort": PINNED_REASONING_EFFORT,
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "jsonschema_version": importlib.metadata.version("jsonschema"),
        },
    }
    write_json(
        condition_root / "condition_metadata.json", condition_metadata
    )

    failures = 0
    for task_id in task_ids:
        task_dir = condition_root / task_id
        task_dir.mkdir()
        catalogue_file = task_catalogue_path(
            repo, task_id, args.size, args.configuration
        )
        catalogue = load_json(catalogue_file)
        prompt = build_child_prompt(
            task_id, tasks[task_id]["prompt_zh"], catalogue
        )
        snapshot = task_dir / "catalogue_snapshot.json"
        write_json(snapshot, catalogue)
        packet = {
            "schema_version": "E1V2-1.0",
            "experiment_id": EXPERIMENT_ID,
            "task_id": task_id,
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "run_id": args.run_id,
            "child_visible_inputs": [
                "current_chinese_task",
                "current_task_conditioned_catalogue",
                "fixed_eight_field_contract",
            ],
            "child_hidden_inputs": [
                "Gold",
                "evaluator",
                "other_tasks",
                "other_sizes",
                "other_configurations",
                "standalone_relations",
                "prior_results",
            ],
            "input_hashes": {
                "task_text_json_sha256": sha256_bytes(
                    json.dumps(
                        tasks[task_id]["prompt_zh"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ),
                "gold_task_json_sha256": sha256_bytes(
                    json.dumps(
                        tasks[task_id],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ),
                "catalogue_source_sha256": sha256_file(catalogue_file),
                "catalogue_snapshot_sha256": sha256_file(snapshot),
                "child_prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            },
        }
        write_json(task_dir / "packet_manifest.json", packet)
        raw_path = task_dir / "raw_response.txt"
        events_path = task_dir / "codex_events.jsonl"
        started = datetime.now(timezone.utc)
        timer = time.monotonic()
        if args.fixture_response_dir:
            fixture = args.fixture_response_dir.resolve() / f"{task_id}.txt"
            command = ["fixture-copy", str(fixture), str(raw_path)]
            child_pid = None
            codex_thread_id = None
            temporary_cwd = None
            thread_id_missing_reason = "fixture_mode_no_codex_process"
            if fixture.is_file():
                shutil.copyfile(fixture, raw_path)
                returncode, stderr = 0, ""
            else:
                write_bytes(raw_path, b"")
                returncode, stderr = 4, f"Missing fixture: {fixture}"
            write_bytes(events_path, b"")
        else:
            with tempfile.TemporaryDirectory(
                prefix=f"skillnet_e1v2_{task_id}_"
            ) as temporary:
                temporary_cwd = str(Path(temporary).resolve())
                (
                    returncode,
                    stderr,
                    command,
                    child_pid,
                    codex_thread_id,
                    thread_id_missing_reason,
                ) = execute_codex(
                    prompt,
                    raw_path.resolve(),
                    events_path,
                    Path(temporary_cwd),
                )
            if not raw_path.exists():
                write_bytes(raw_path, b"")
        validation, prediction = validate_raw(raw_path, schema, task_id)
        write_json(task_dir / "schema_validation.json", validation)
        if prediction is not None:
            write_json(task_dir / "prediction.json", prediction)
        metadata = {
            "schema_version": "E1V2-1.0",
            "experiment_id": EXPERIMENT_ID,
            "task_id": task_id,
            "configuration": args.configuration,
            "catalogue_size": args.size,
            "run_id": args.run_id,
            "execution_mode": condition_metadata["execution_mode"],
            "attempt_number": 1,
            "automatic_retry": False,
            "child_pid": child_pid,
            "codex_thread_id": codex_thread_id,
            "thread_id_missing_reason": thread_id_missing_reason,
            "temporary_cwd": temporary_cwd,
            "start_time": started.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.monotonic() - timer, 6),
            "exit_code": returncode,
            "command": command,
            "command_redacted": command,
            "stderr": stderr,
            "raw_response_sha256": sha256_file(raw_path),
            "codex_events_sha256": sha256_file(events_path),
            "prediction_saved": prediction is not None,
            "input_hashes": packet["input_hashes"],
        }
        write_json(task_dir / "run_metadata.json", metadata)
        failures += int(returncode != 0)

    print(
        json.dumps(
            {
                "experiment_id": EXPERIMENT_ID,
                "run_root": str(condition_root),
                "task_count": len(task_ids),
                "execution_mode": condition_metadata["execution_mode"],
                "child_process_failures": failures,
                "formal_model_tasks_started": (
                    len(task_ids) if args.execute else 0
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if failures == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
