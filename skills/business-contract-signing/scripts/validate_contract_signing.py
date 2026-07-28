#!/usr/bin/env python3
"""Validate contract signature readiness without performing signature actions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_TERMS = (
    "scope",
    "pricing",
    "delivery",
    "acceptance",
    "payment",
    "confidentiality",
    "data_security",
    "intellectual_property",
    "liability",
    "change_control",
    "termination",
    "dispute_resolution",
)


def _required_text(data: dict[str, Any], *fields: str) -> None:
    missing = [field for field in fields if not str(data.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")


def _object_list(data: dict[str, Any], field: str, *, allow_empty: bool = False) -> list[dict[str, Any]]:
    value = data.get(field)
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"{field} must be a {'list' if allow_empty else 'non-empty list'}")
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{field} entries must be objects")
    return value


def validate_contract_signing(data: dict[str, Any]) -> dict[str, Any]:
    """Return readiness findings while preserving the human signature boundary."""
    if not isinstance(data, dict):
        raise ValueError("contract packet must be an object")
    _required_text(
        data,
        "contract_id",
        "customer_id",
        "opportunity_id",
        "quotation_id",
        "contract_version",
        "document_digest",
    )
    digest = str(data["document_digest"]).strip()
    if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise ValueError("document_digest must be sha256 followed by 64 hexadecimal characters")

    findings: list[str] = []
    counterparties = _object_list(data, "counterparties")
    party_ids: set[str] = set()
    normalized_parties: list[dict[str, str]] = []
    for party in counterparties:
        _required_text(party, "party_id", "legal_name", "role")
        party_id = str(party["party_id"]).strip()
        if party_id in party_ids:
            raise ValueError(f"duplicate party_id: {party_id}")
        party_ids.add(party_id)
        normalized_parties.append(
            {"party_id": party_id, "legal_name": str(party["legal_name"]).strip(), "role": str(party["role"]).strip()}
        )

    signatories = _object_list(data, "signatories", allow_empty=True)
    signatory_by_party: dict[str, dict[str, Any]] = {}
    for signatory in signatories:
        _required_text(signatory, "party_id", "name")
        party_id = str(signatory["party_id"]).strip()
        if party_id not in party_ids:
            raise ValueError(f"signatory references unknown party: {party_id}")
        if party_id in signatory_by_party:
            raise ValueError(f"duplicate signatory party: {party_id}")
        signatory_by_party[party_id] = signatory
    for party_id in sorted(party_ids):
        signatory = signatory_by_party.get(party_id)
        if signatory is None:
            findings.append(f"missing signatory for party: {party_id}")
        elif not str(signatory.get("authority_reference", "")).strip():
            findings.append(f"missing signatory authority for party: {party_id}")

    required_approvals = data.get("required_approvals")
    if not isinstance(required_approvals, list) or not required_approvals:
        raise ValueError("required_approvals must be a non-empty list")
    required_names = [str(item).strip().lower() for item in required_approvals]
    if any(not name for name in required_names) or len(set(required_names)) != len(required_names):
        raise ValueError("required_approvals must contain unique non-empty names")
    approvals = _object_list(data, "approvals", allow_empty=True)
    approval_by_type: dict[str, dict[str, Any]] = {}
    for approval in approvals:
        _required_text(approval, "approval_type", "status")
        approval_type = str(approval["approval_type"]).strip().lower()
        if approval_type in approval_by_type:
            raise ValueError(f"duplicate approval type: {approval_type}")
        approval_by_type[approval_type] = approval
    for approval_type in required_names:
        approval = approval_by_type.get(approval_type)
        if (
            approval is None
            or str(approval.get("status", "")).strip().lower() != "approved"
            or not str(approval.get("evidence_reference", "")).strip()
        ):
            findings.append(f"missing approved evidence for: {approval_type}")

    deviations = _object_list(data, "negotiation_deviations", allow_empty=True)
    deviation_ids: set[str] = set()
    for deviation in deviations:
        _required_text(deviation, "deviation_id", "status", "evidence_reference")
        deviation_id = str(deviation["deviation_id"]).strip()
        if deviation_id in deviation_ids:
            raise ValueError(f"duplicate deviation_id: {deviation_id}")
        deviation_ids.add(deviation_id)
        if str(deviation["status"]).strip().lower() not in {"resolved", "approved"}:
            findings.append(f"unresolved negotiation deviation: {deviation_id}")

    terms = data.get("terms")
    if not isinstance(terms, dict):
        raise ValueError("terms must be an object")
    for term in REQUIRED_TERMS:
        if not str(terms.get(term, "")).strip():
            findings.append(f"missing required term: {term}")

    passed = not findings
    return {
        "contract_id": str(data["contract_id"]).strip(),
        "customer_id": str(data["customer_id"]).strip(),
        "opportunity_id": str(data["opportunity_id"]).strip(),
        "quotation_id": str(data["quotation_id"]).strip(),
        "contract_version": str(data["contract_version"]).strip(),
        "document_digest": digest.lower(),
        "counterparties": normalized_parties,
        "required_approvals": required_names,
        "blocking_findings": findings,
        "automated_readiness_passed": passed,
        "signature_status": "ready_for_human_signature" if passed else "blocked",
        "external_action": "not_performed",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a contract packet without signing or transmitting it."
    )
    parser.add_argument("--data", required=True, type=Path, help="Contract packet JSON")
    args = parser.parse_args()
    payload = json.loads(args.data.read_text(encoding="utf-8"))
    print(json.dumps(validate_contract_signing(payload), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
