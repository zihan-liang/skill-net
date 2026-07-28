#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "procurement-contract-order"
    / "scripts"
    / "render_purchase_order.py"
)
SPEC = spec_from_file_location("render_purchase_order", SCRIPT)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PurchaseOrderRenderingTests(unittest.TestCase):
    def setUp(self):
        self.template = """# DRAFT — NOT ISSUED

Order: {{order_id}}
Contract: {{contract_id}}
Request: {{request_id}}
Selection: {{selection_id}}
Supplier: {{supplier_legal_name}} ({{supplier_id}})
Buyer: {{buyer_name}}
Order date: {{order_date}}
Delivery: {{delivery_date}} to {{delivery_location}}

{{line_items_table}}

Subtotal: {{subtotal}} {{currency}}
Payment: {{payment_terms}}
Acceptance: {{acceptance_criteria}}
Selection approval: {{selection_approval_reference}}
Order approval: {{order_approval_reference}}
"""
        self.data = {
            "order_id": "PO-1",
            "contract_id": "CON-1",
            "request_id": "REQ-1",
            "selection_id": "SEL-1",
            "supplier_id": "SUP-1",
            "supplier_legal_name": "Example Supplier Ltd.",
            "buyer_name": "Example Startup",
            "order_date": "2026-07-28",
            "delivery_date": "2026-08-15",
            "delivery_location": "Shanghai",
            "currency": "CNY",
            "payment_terms": "30 days after acceptance",
            "acceptance_criteria": "Quantity and specification inspection",
            "selection_approved": True,
            "selection_approval_reference": "APP-SEL-1",
            "order_approved": True,
            "order_approval_reference": "APP-PO-1",
            "line_items": [
                {
                    "line_id": "1",
                    "description": "Laptop",
                    "quantity": "2",
                    "unit": "unit",
                    "unit_price": "100.00",
                }
            ],
        }

    def test_renders_approved_order_with_hand_checked_total(self):
        rendered = MODULE.render_purchase_order(self.template, self.data)

        self.assertIn("# DRAFT — NOT ISSUED", rendered)
        self.assertIn("Order: PO-1", rendered)
        self.assertIn("| 1 | Laptop | 2 | unit | 100.00 | 200.00 |", rendered)
        self.assertIn("Subtotal: 200.00 CNY", rendered)

    def test_requires_approved_supplier_selection(self):
        data = {**self.data, "selection_approved": False}

        with self.assertRaisesRegex(ValueError, "supplier selection approval required"):
            MODULE.render_purchase_order(self.template, data)

    def test_requires_order_release_approval(self):
        data = {**self.data, "order_approved": False}

        with self.assertRaisesRegex(ValueError, "order release approval required"):
            MODULE.render_purchase_order(self.template, data)

    def test_rejects_missing_required_value(self):
        data = {**self.data, "supplier_legal_name": ""}

        with self.assertRaisesRegex(ValueError, "missing purchase order fields"):
            MODULE.render_purchase_order(self.template, data)

    def test_rejects_unresolved_template_placeholder(self):
        template = self.template + "\nUnknown: {{unknown_value}}\n"

        with self.assertRaisesRegex(ValueError, "unresolved template fields: unknown_value"):
            MODULE.render_purchase_order(template, self.data)

    def test_rejects_non_positive_line_price(self):
        data = {
            **self.data,
            "line_items": [{**self.data["line_items"][0], "unit_price": "-1"}],
        }

        with self.assertRaisesRegex(ValueError, "unit_price must be positive"):
            MODULE.render_purchase_order(self.template, data)


if __name__ == "__main__":
    unittest.main()
