#!/usr/bin/env python3
"""Create a transparent, job-related five-dimension resume scorecard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "essential_capabilities",
    "relevant_experience",
    "evidence_of_impact",
    "domain_context",
    "learning_and_collaboration",
)
PROTECTED_KEYS = {
    "age",
    "birth_date",
    "disability",
    "ethnicity",
    "family_status",
    "gender",
    "marital_status",
    "nationality",
    "photo",
    "race",
    "religion",
}


def _find_protected_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().strip()
            if normalized in PROTECTED_KEYS:
                found.add(normalized)
            found.update(_find_protected_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_protected_keys(child))
    return found


def score_resume(criteria: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    protected = _find_protected_keys(candidate)
    if protected:
        names = ", ".join(sorted(protected))
        raise ValueError(f"candidate contains protected or non-job-related fields: {names}")

    configured = criteria.get("dimensions", {})
    missing_criteria = [name for name in DIMENSIONS if name not in configured]
    if missing_criteria:
        raise ValueError(f"criteria missing dimensions: {', '.join(missing_criteria)}")

    weights = {name: float(configured[name].get("weight", 0)) for name in DIMENSIONS}
    if any(weight < 0 for weight in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("dimension weights must be non-negative with a positive total")
    weight_total = sum(weights.values())
    normalized = {name: weight / weight_total for name, weight in weights.items()}

    evidence = candidate.get("evidence", {})
    dimension_results: dict[str, dict[str, Any]] = {}
    missing_dimensions: list[str] = []
    weighted_score = 0.0
    coverage = 0.0

    for name in DIMENSIONS:
        item = evidence.get(name)
        if not item or item.get("score") is None or not str(item.get("evidence", "")).strip():
            missing_dimensions.append(name)
            dimension_results[name] = {
                "score": None,
                "evidence": None,
                "weight": round(normalized[name], 4),
                "contribution": 0.0,
            }
            continue

        score = float(item["score"])
        if not 0 <= score <= 5:
            raise ValueError(f"{name} score must be between 0 and 5")
        contribution = score * normalized[name]
        weighted_score += contribution
        coverage += normalized[name]
        dimension_results[name] = {
            "score": score,
            "evidence": str(item["evidence"]).strip(),
            "source": item.get("source"),
            "weight": round(normalized[name], 4),
            "contribution": round(contribution, 2),
        }

    if coverage < 0.70:
        band = "insufficient_evidence"
    elif weighted_score >= 4.0:
        band = "strong_match"
    elif weighted_score >= 3.0:
        band = "match"
    elif weighted_score >= 2.0:
        band = "partial_match"
    else:
        band = "weak_match"

    return {
        "candidate_id": candidate.get("candidate_id"),
        "dimensions": dimension_results,
        "weighted_score": round(weighted_score, 2),
        "evidence_coverage": round(coverage, 2),
        "missing_dimensions": missing_dimensions,
        "recommendation_band": band,
        "decision_status": "human_review_required",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--criteria", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    criteria = json.loads(args.criteria.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    rendered = json.dumps(score_resume(criteria, candidate), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
