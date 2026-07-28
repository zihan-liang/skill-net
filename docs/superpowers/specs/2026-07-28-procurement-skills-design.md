# Procurement Skills Design — Current Atomic Catalog

The procurement department owns twelve atomic Skills:

1. `procurement-requirement`
2. `procurement-supplier-search`
3. `procurement-supplier-qualification`
4. `procurement-rfq-generation`
5. `procurement-quote-comparison`
6. `procurement-supplier-scoring`
7. `procurement-supplier-selection`
8. `procurement-contract-generation`
9. `procurement-purchase-order`
10. `procurement-delivery-tracking`
11. `procurement-delivery-acceptance`
12. `procurement-supplier-evaluation`

End-to-end order: requirement → `finance-budget-check` → search → qualification → RFQ → commercial comparison → supplier scoring → selection → contract → PO → tracking → acceptance → `finance-invoice-verification` → `finance-payment-approval` → supplier evaluation.

Supplier records use stable IDs, minimum allowlisted fields, restricted attachment references, explicit human confirmation, and append-only audit evidence inside the relevant stages. All packages live under `.agents/skills/`.
