#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "hr-offer-generator"
    / "scripts"
    / "generate_offer.py"
)
SPEC = spec_from_file_location("generate_offer", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GenerateOfferTests(unittest.TestCase):
    def setUp(self):
        self.template = "Offer for {{candidate_name}} as {{job_title}} at {{base_salary}} {{currency}}."
        self.data = {
            "candidate_name": "Lin Chen",
            "job_title": "AI Product Manager",
            "base_salary": "30000",
            "currency": "CNY",
            "compensation_approved": True,
            "offer_approved": True,
        }

    def test_renders_approved_offer_fields(self):
        rendered = MODULE.render_offer(self.data, self.template)

        self.assertEqual(rendered, "Offer for Lin Chen as AI Product Manager at 30000 CNY.")

    def test_rejects_unapproved_compensation(self):
        self.data["compensation_approved"] = False

        with self.assertRaisesRegex(ValueError, "compensation approval"):
            MODULE.render_offer(self.data, self.template)

    def test_rejects_unresolved_template_fields(self):
        template = self.template + " Start: {{start_date}}"

        with self.assertRaisesRegex(ValueError, "missing template values: start_date"):
            MODULE.render_offer(self.data, template)


if __name__ == "__main__":
    unittest.main()
