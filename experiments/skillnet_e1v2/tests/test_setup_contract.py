#!/usr/bin/env python3
"""Frozen candidate-pool and Catalogue contract tests for SkillNet E1-v2."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
E1V2_GOLD = ROOT / "SkillNet_Gold_Tasks_V4" / "e1v2" / "E1V2_Gold_21.json"
SOURCE_GOLD = (
    ROOT / "SkillNet_Gold_Tasks_V4" / "02_Gold_Standard_21_V4.json"
)
POOL_MANIFEST = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "e1v2_catalogues"
    / "candidate_pool_manifest.json"
)
CATALOGUE_ROOT = (
    ROOT / "skillnet_run_guide_v1_1" / "e1v2_catalogues"
)
FULL_A = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "catalogues"
    / "size_46"
    / "A_flat_catalogue.json"
)
FULL_C = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "catalogues"
    / "size_46"
    / "C_graph_structured_catalogue.json"
)

FILES = {
    "A": "A_flat_catalogue.json",
    "B": "B_department_grouped_catalogue.json",
    "C": "C_graph_structured_catalogue.json",
}
ENDPOINTS = {
    "prerequisite": ("before", "after"),
    "conflict": ("gate_skill", "blocked_skill"),
    "mutex": ("skill_a", "skill_b"),
    "enhances": ("source", "target"),
}
FORBIDDEN_CATALOGUE_KEYS = {
    "required_skills",
    "optional_skills",
    "forbidden_skills",
    "canonical_sequence",
    "hard_order_constraints",
    "initial_skill_states",
    "expected_blocked_by",
    "expected_route_choice",
    "task_constraints",
    "gold",
    "gold_answer",
    "prompt_zh",
    "prompt_en",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_hash(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def flatten(catalogue: dict) -> list[dict]:
    if catalogue["configuration"] == "A":
        return catalogue["skills"]
    return [
        card
        for department in catalogue["departments"]
        for card in department["skills"]
    ]


def recursive_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(recursive_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(recursive_keys(item))
    return keys


def induced_relations(full: dict, skill_ids: set[str]) -> dict:
    output = {}
    for relation_type, records in full["relations"].items():
        left, right = ENDPOINTS[relation_type]
        output[relation_type] = [
            record
            for record in records
            if record[left] in skill_ids and record[right] in skill_ids
        ]
    return output


class E1V2SetupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gold = load(E1V2_GOLD)
        cls.source_gold = load(SOURCE_GOLD)
        cls.pool_manifest = load(POOL_MANIFEST)
        cls.full_a = load(FULL_A)
        cls.full_c = load(FULL_C)
        cls.tasks = {task["task_id"]: task for task in cls.gold["tasks"]}
        cls.pool_tasks = {
            task["task_id"]: task for task in cls.pool_manifest["tasks"]
        }

    def test_exactly_21_unique_tasks_with_18_original_and_3_short(self) -> None:
        self.assertEqual(21, len(self.tasks))
        self.assertEqual(21, len(self.pool_tasks))
        self.assertEqual(set(self.tasks), set(self.pool_tasks))
        origins = [record["task_origin"] for record in self.pool_tasks.values()]
        self.assertEqual(18, origins.count("original_compatible"))
        self.assertEqual(3, origins.count("new_scale_compatible_short"))
        self.assertEqual(
            {"GT03_PROC_GOAL", "GT07_CROSS_CUSTOM_TECH_SUPPLIER",
             "GT12_CROSS_BUSINESS_TO_PO"},
            {
                record["source_task_id"]
                for record in self.pool_tasks.values()
                if record["task_origin"] == "new_scale_compatible_short"
            },
        )
        source_tasks = {
            task["task_id"]: task for task in self.source_gold["tasks"]
        }
        for task_id, record in self.pool_tasks.items():
            if record["task_origin"] == "original_compatible":
                self.assertEqual(source_tasks[task_id], self.tasks[task_id])
        self.assertFalse(
            {
                "GT03_PROC_GOAL",
                "GT07_CROSS_CUSTOM_TECH_SUPPLIER",
                "GT12_CROSS_BUSINESS_TO_PO",
            }
            & set(self.tasks)
        )

    def test_gold_relevant_skills_fit_and_are_in_s10(self) -> None:
        for task_id, record in self.pool_tasks.items():
            relevant = record["gold_relevant_skills"]["skill_ids"]
            self.assertEqual(len(relevant), record["gold_relevant_skills"]["count"])
            self.assertLessEqual(len(relevant), 10, task_id)
            self.assertTrue(
                set(relevant) <= set(record["pools"]["10"]["skill_ids"]),
                task_id,
            )
            self.assertTrue(record["gold_relevant_skills"]["sources_complete"])

    def test_pool_sizes_hashes_and_strict_nesting(self) -> None:
        for task_id, record in self.pool_tasks.items():
            pools = record["pools"]
            for size in ("10", "30", "46"):
                ids = pools[size]["skill_ids"]
                self.assertEqual(int(size), len(ids), (task_id, size))
                self.assertEqual(len(ids), len(set(ids)), (task_id, size))
                self.assertEqual(stable_hash(ids), pools[size]["skill_ids_sha256"])
            self.assertLess(set(pools["10"]["skill_ids"]), set(pools["30"]["skill_ids"]))
            self.assertLess(set(pools["30"]["skill_ids"]), set(pools["46"]["skill_ids"]))
            self.assertEqual(
                {card["skill_id"] for card in self.full_a["skills"]},
                set(pools["46"]["skill_ids"]),
            )

    def test_cross_scale_task_and_gold_hashes_are_identical(self) -> None:
        for task_id, record in self.pool_tasks.items():
            task = self.tasks[task_id]
            self.assertEqual(stable_hash(task), record["gold_json_sha256"])
            self.assertEqual(
                stable_hash(task["prompt_zh"]), record["task_text_json_sha256"]
            )
            self.assertEqual(
                1,
                len(
                    {
                        record["pools"][size]["gold_json_sha256"]
                        for size in ("10", "30", "46")
                    }
                ),
            )
            self.assertEqual(
                1,
                len(
                    {
                        record["pools"][size]["task_text_json_sha256"]
                        for size in ("10", "30", "46")
                    }
                ),
            )

    def test_abc_skill_sets_cards_structure_and_induced_graph(self) -> None:
        for task_id, record in self.pool_tasks.items():
            for size in ("10", "30", "46"):
                base = CATALOGUE_ROOT / "tasks" / task_id / f"size_{size}"
                catalogues = {key: load(base / filename) for key, filename in FILES.items()}
                cards = {key: flatten(value) for key, value in catalogues.items()}
                id_sets = {
                    key: {card["skill_id"] for card in values}
                    for key, values in cards.items()
                }
                self.assertEqual(id_sets["A"], id_sets["B"], (task_id, size))
                self.assertEqual(id_sets["B"], id_sets["C"], (task_id, size))
                normalized_cards = {
                    key: {card["skill_id"]: card for card in values}
                    for key, values in cards.items()
                }
                self.assertEqual(normalized_cards["A"], normalized_cards["B"])
                self.assertEqual(normalized_cards["B"], normalized_cards["C"])
                self.assertNotIn("departments", catalogues["A"])
                self.assertNotIn("relations", catalogues["A"])
                self.assertNotIn("relation_semantics", catalogues["A"])
                self.assertNotIn("relations", catalogues["B"])
                self.assertNotIn("relation_semantics", catalogues["B"])
                self.assertEqual(
                    catalogues["C"]["relations"],
                    induced_relations(self.full_c, id_sets["C"]),
                    (task_id, size),
                )
                for records in catalogues["C"]["relations"].values():
                    for relation in records:
                        endpoints = set(relation.values()) & id_sets["C"]
                        self.assertGreaterEqual(len(endpoints), 2)
                for catalogue in catalogues.values():
                    self.assertFalse(
                        recursive_keys(catalogue) & FORBIDDEN_CATALOGUE_KEYS,
                        (task_id, size, catalogue["configuration"]),
                    )


if __name__ == "__main__":
    unittest.main()
