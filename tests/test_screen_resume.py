#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "hr-resume-screening"
    / "scripts"
    / "screen_resume.py"
)
SPEC = spec_from_file_location("screen_resume", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ScreenResumeTests(unittest.TestCase):
    def setUp(self):
        self.criteria = {
            "dimensions": {
                "essential_capabilities": {"weight": 0.30},
                "relevant_experience": {"weight": 0.20},
                "evidence_of_impact": {"weight": 0.20},
                "domain_context": {"weight": 0.15},
                "learning_and_collaboration": {"weight": 0.15},
            }
        }

    def test_scores_five_dimensions_with_evidence(self):
        candidate = {
            "candidate_id": "C-001",
            "evidence": {
                "essential_capabilities": {"score": 5, "evidence": "Built two production agents"},
                "relevant_experience": {"score": 4, "evidence": "Three years in AI products"},
                "evidence_of_impact": {"score": 4, "evidence": "Improved activation by 18%"},
                "domain_context": {"score": 3, "evidence": "Consumer app internship"},
                "learning_and_collaboration": {"score": 4, "evidence": "Led cross-functional launch"},
            },
        }

        result = MODULE.score_resume(self.criteria, candidate)

        self.assertEqual(result["candidate_id"], "C-001")
        self.assertEqual(result["weighted_score"], 4.15)
        self.assertEqual(result["evidence_coverage"], 1.0)
        self.assertEqual(result["recommendation_band"], "strong_match")

    def test_marks_missing_evidence_without_inventing_a_score(self):
        candidate = {
            "candidate_id": "C-002",
            "evidence": {
                "essential_capabilities": {"score": 4, "evidence": "Python portfolio"},
            },
        }

        result = MODULE.score_resume(self.criteria, candidate)

        self.assertIn("relevant_experience", result["missing_dimensions"])
        self.assertEqual(result["evidence_coverage"], 0.3)
        self.assertEqual(result["recommendation_band"], "insufficient_evidence")
        self.assertIsNone(result["dimensions"]["relevant_experience"]["score"])

    def test_rejects_protected_characteristics(self):
        candidate = {"candidate_id": "C-003", "age": 29, "evidence": {}}

        with self.assertRaisesRegex(ValueError, "protected or non-job-related"):
            MODULE.score_resume(self.criteria, candidate)


if __name__ == "__main__":
    unittest.main()
