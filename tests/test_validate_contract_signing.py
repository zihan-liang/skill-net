#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "business-contract-signing"
    / "scripts"
    / "validate_contract_signing.py"
)
SPEC = spec_from_file_location("validate_contract_signing", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ContractSigningValidationTests(unittest.TestCase):
    def setUp(self):
        self.packet = {
            "contract_id": "CON-1",
            "customer_id": "CUS-1",
            "opportunity_id": "OPP-1",
            "quotation_id": "QUOTE-1",
            "contract_version": "3",
            "document_digest": "sha256:" + "b" * 64,
            "counterparties": [
                {"party_id": "COMPANY", "legal_name": "Fictional Platform Co.", "role": "provider"},
                {"party_id": "CUSTOMER", "legal_name": "Fictional Merchant Co.", "role": "customer"},
            ],
            "signatories": [
                {"party_id": "COMPANY", "name": "Authorized Provider", "authority_reference": "AUTH-COMPANY"},
                {"party_id": "CUSTOMER", "name": "Authorized Customer", "authority_reference": "AUTH-CUSTOMER"},
            ],
            "required_approvals": ["business", "legal", "finance"],
            "approvals": [
                {"approval_type": "business", "status": "approved", "evidence_reference": "APP-BUS"},
                {"approval_type": "legal", "status": "approved", "evidence_reference": "APP-LEGAL"},
                {"approval_type": "finance", "status": "approved", "evidence_reference": "APP-FIN"},
            ],
            "negotiation_deviations": [
                {"deviation_id": "DEV-1", "status": "resolved", "evidence_reference": "NEG-1"}
            ],
            "terms": {
                "scope": "TERM-SCOPE",
                "pricing": "TERM-PRICE",
                "delivery": "TERM-DELIVERY",
                "acceptance": "TERM-ACCEPT",
                "payment": "TERM-PAYMENT",
                "confidentiality": "TERM-CONF",
                "data_security": "TERM-DATA",
                "intellectual_property": "TERM-IP",
                "liability": "TERM-LIABILITY",
                "change_control": "TERM-CHANGE",
                "termination": "TERM-TERMINATION",
                "dispute_resolution": "TERM-DISPUTE",
            },
        }

    def test_complete_packet_is_ready_for_human_signature_only(self):
        result = MODULE.validate_contract_signing(self.packet)

        self.assertTrue(result["automated_readiness_passed"])
        self.assertEqual(result["signature_status"], "ready_for_human_signature")
        self.assertEqual(result["external_action"], "not_performed")

    def test_missing_required_approval_blocks_signature(self):
        approvals = self.packet["approvals"][:-1]

        result = MODULE.validate_contract_signing({**self.packet, "approvals": approvals})

        self.assertFalse(result["automated_readiness_passed"])
        self.assertIn("missing approved evidence for: finance", result["blocking_findings"])
        self.assertEqual(result["signature_status"], "blocked")

    def test_unresolved_negotiation_deviation_blocks_signature(self):
        deviations = [{"deviation_id": "DEV-1", "status": "open", "evidence_reference": "NEG-1"}]

        result = MODULE.validate_contract_signing(
            {**self.packet, "negotiation_deviations": deviations}
        )

        self.assertIn("unresolved negotiation deviation: DEV-1", result["blocking_findings"])

    def test_rejects_malformed_document_digest(self):
        with self.assertRaisesRegex(ValueError, "document_digest must be sha256"):
            MODULE.validate_contract_signing({**self.packet, "document_digest": "latest"})

    def test_missing_required_term_blocks_signature(self):
        terms = dict(self.packet["terms"])
        terms.pop("liability")

        result = MODULE.validate_contract_signing({**self.packet, "terms": terms})

        self.assertIn("missing required term: liability", result["blocking_findings"])

    def test_missing_signatory_authority_blocks_signature(self):
        signatories = [
            self.packet["signatories"][0],
            {**self.packet["signatories"][1], "authority_reference": ""},
        ]

        result = MODULE.validate_contract_signing({**self.packet, "signatories": signatories})

        self.assertIn("missing signatory authority for party: CUSTOMER", result["blocking_findings"])

    def test_missing_counterparty_signatory_blocks_signature(self):
        result = MODULE.validate_contract_signing(
            {**self.packet, "signatories": [self.packet["signatories"][0]]}
        )

        self.assertIn("missing signatory for party: CUSTOMER", result["blocking_findings"])


if __name__ == "__main__":
    unittest.main()
