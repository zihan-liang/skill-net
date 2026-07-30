#!/usr/bin/env python3
"""PRE-RUN AMENDMENT regression tests for freeze and evidence contracts."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
E1V2_DIR = ROOT / "experiments" / "skillnet_e1v2"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify_setup = import_module(
    "verify_setup_e1v2",
    E1V2_DIR / "verify_setup.py",
)


class E1V2PreRunAmendmentTests(unittest.TestCase):
    def test_two_layer_freeze_accepts_direct_child_evidence_only(self) -> None:
        report = verify_setup.assess_freeze_identity(
            local_head="b" * 40,
            origin_head="b" * 40,
            direct_parent="a" * 40,
            official_setup_content_commit="a" * 40,
            changed_paths=[
                "experiments/skillnet_e1v2/setup_evidence/"
                "setup_freeze_manifest.json",
                "experiments/skillnet_e1v2/implementation_records/"
                "E1V2-PRE-RUN-AMENDMENT.md",
            ],
            working_tree_clean=True,
        )
        self.assertTrue(report["valid"])
        self.assertTrue(
            report["checks"]["head_is_not_setup_content_commit"]
        )

    def test_two_layer_freeze_rejects_self_reference_or_content_diff(
        self,
    ) -> None:
        report = verify_setup.assess_freeze_identity(
            local_head="a" * 40,
            origin_head="a" * 40,
            direct_parent="0" * 40,
            official_setup_content_commit="a" * 40,
            changed_paths=[
                "experiments/skillnet_e1v2/run_condition.py"
            ],
            working_tree_clean=True,
        )
        self.assertFalse(report["valid"])
        self.assertFalse(
            report["checks"][
                "head_direct_parent_equals_official_setup_content_commit"
            ]
        )
        self.assertFalse(
            report["checks"][
                "freeze_record_diff_only_contains_allowed_evidence"
            ]
        )
        self.assertFalse(
            report["checks"]["head_is_not_setup_content_commit"]
        )

    def test_metric_definition_marks_new_count_as_analysis_only(
        self,
    ) -> None:
        specification = json.loads(
            (E1V2_DIR / "metric_definitions.json").read_text(
                encoding="utf-8"
            )
        )
        definition = specification["analysis_counts"][
            "skill_routing_true_control_false"
        ]
        self.assertFalse(definition["failure_gate"])
        self.assertFalse(definition["changes_per_task_success_semantics"])
        self.assertIn(
            "skill_routing_true_control_false",
            specification["condition_consistency_categories"],
        )


if __name__ == "__main__":
    unittest.main()
