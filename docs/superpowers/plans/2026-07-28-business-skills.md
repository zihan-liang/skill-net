# Business Skills — Current Implementation Manifest

Canonical location: `.agents/skills/`.

Packages: `business-customer-lead`, `business-requirement-communication`, `business-opportunity-assessment`, `business-solution-quotation`, `business-negotiation`, `business-contract-signing`, `business-project-delivery-tracking`, `business-acceptance`, and `business-renewal`.

Verification: run `python3 -m unittest tests.test_business_skills tests.test_evaluate_opportunity tests.test_calculate_quotation tests.test_validate_contract_signing tests.test_evaluate_delivery_progress -v`, the catalog contract, every script syntax check, and the full suite.
