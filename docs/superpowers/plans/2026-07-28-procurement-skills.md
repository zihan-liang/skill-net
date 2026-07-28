# Procurement Skills — Current Implementation Manifest

Canonical location: `.agents/skills/`.

Packages: `procurement-requirement`, `procurement-supplier-search`, `procurement-supplier-qualification`, `procurement-rfq-generation`, `procurement-quote-comparison`, `procurement-supplier-scoring`, `procurement-supplier-selection`, `procurement-contract-generation`, `procurement-purchase-order`, `procurement-delivery-tracking`, `procurement-delivery-acceptance`, and `procurement-supplier-evaluation`.

Verification: run `python3 -m unittest tests.test_procurement_skills tests.test_compare_quotes tests.test_score_suppliers tests.test_render_purchase_order tests.test_evaluate_supplier -v`, the catalog contract, every script syntax check, and the full suite.
