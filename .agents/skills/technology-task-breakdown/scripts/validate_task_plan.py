#!/usr/bin/env python3
"""Validate a technology task plan and return a deterministic dependency order."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import heapq
import json
from pathlib import Path
from typing import Any


TWO_PLACES = Decimal("0.01")


def _positive_decimal(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a valid number") from None
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{field} must be positive")
    return number


def validate_task_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate task fields and dependencies without assigning or scheduling work."""
    required_plan = ("task_plan_id", "design_id", "design_approval_reference", "tasks")
    missing_plan = [field for field in required_plan if plan.get(field) in (None, "")]
    if missing_plan:
        raise ValueError(f"missing task plan fields: {', '.join(missing_plan)}")
    tasks = plan["tasks"]
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a non-empty list")

    required_task = (
        "task_id",
        "title",
        "owner",
        "deliverable",
        "acceptance_criteria",
        "estimate_hours",
        "dependencies",
    )
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = Decimal("0")
    for task in tasks:
        missing = [field for field in required_task if task.get(field) in (None, "")]
        if missing:
            raise ValueError(f"missing task fields: {', '.join(missing)}")
        task_id = str(task["task_id"]).strip()
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        criteria = task["acceptance_criteria"]
        if (
            not isinstance(criteria, list)
            or not criteria
            or any(not str(item).strip() for item in criteria)
        ):
            raise ValueError("acceptance_criteria must be a non-empty list")
        dependencies = task["dependencies"]
        if not isinstance(dependencies, list):
            raise ValueError("dependencies must be a list")
        cleaned_dependencies = [str(value).strip() for value in dependencies]
        if any(not value for value in cleaned_dependencies):
            raise ValueError("dependencies must not contain blank IDs")
        if len(set(cleaned_dependencies)) != len(cleaned_dependencies):
            raise ValueError(f"duplicate dependency in task {task_id}")
        estimate = _positive_decimal(task["estimate_hours"], "estimate_hours")
        total += estimate
        normalized.append(
            {
                "task_id": task_id,
                "title": str(task["title"]).strip(),
                "owner": str(task["owner"]).strip(),
                "deliverable": str(task["deliverable"]).strip(),
                "acceptance_criteria": [str(item).strip() for item in criteria],
                "estimate_hours": format(estimate, "f"),
                "dependencies": cleaned_dependencies,
            }
        )

    task_ids = {task["task_id"] for task in normalized}
    for task in normalized:
        for dependency in task["dependencies"]:
            if dependency not in task_ids:
                raise ValueError(
                    f"unknown dependency {dependency} for task {task['task_id']}"
                )

    indegree = {task_id: 0 for task_id in task_ids}
    downstream = {task_id: [] for task_id in task_ids}
    edges: list[dict[str, str]] = []
    for task in normalized:
        for dependency in task["dependencies"]:
            indegree[task["task_id"]] += 1
            downstream[dependency].append(task["task_id"])
            edges.append({"from": dependency, "to": task["task_id"]})

    ready = [task_id for task_id, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        task_id = heapq.heappop(ready)
        order.append(task_id)
        for next_id in sorted(downstream[task_id]):
            indegree[next_id] -= 1
            if indegree[next_id] == 0:
                heapq.heappush(ready, next_id)
    if len(order) != len(task_ids):
        raise ValueError("task dependency cycle detected")

    return {
        "task_plan_id": str(plan["task_plan_id"]),
        "design_id": str(plan["design_id"]),
        "design_approval_reference": str(plan["design_approval_reference"]),
        "tasks": normalized,
        "task_count": len(normalized),
        "dependency_edges": sorted(edges, key=lambda edge: (edge["from"], edge["to"])),
        "execution_order": order,
        "total_estimate_hours": format(
            total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP), "f"
        ),
        "blocking_findings": [],
        "assignment_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path, help="Task-plan JSON")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    print(json.dumps(validate_task_plan(plan), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
