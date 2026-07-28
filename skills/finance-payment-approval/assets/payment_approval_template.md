# Payment Approval Packet

- Payment ID: {{payment_id}}
- Expense ID: {{expense_id}}
- Invoice ID: {{invoice_id}}
- Department ID: {{department_id}}
- Requested release date: {{release_date}}

## Payee and amount

- Payee ID: {{payee_id}}
- Payee name: {{payee_name}}
- Amount: {{amount}}
- Currency: {{currency}}
- Payment purpose: {{payment_purpose}}
- Contract or order reference: {{contract_reference}}

## Verification evidence

- Expense-review status and evidence: {{expense_review}}
- Invoice-verification status and evidence: {{invoice_verification}}
- Delivery or milestone evidence: {{delivery_evidence}}
- Restricted bank-detail verification reference: {{bank_verification_reference}}
- Duplicate-payment check: {{duplicate_check}}

## Segregation of duties

- Requester: {{requester}}
- Expense reviewer: {{expense_reviewer}}
- Payment approver: {{payment_approver}}
- Payment releaser: {{payment_releaser}}
- Conflict status: {{conflict_status}}

## Approval route

| Stage | Owner | Status | Timestamp | Evidence reference |
|---|---|---|---|---|
| Finance validation | {{owner}} | Draft |  | {{evidence_reference}} |
| Authorized approval | {{owner}} | Draft |  | {{evidence_reference}} |
| Release confirmation | {{owner}} | Not released |  | {{evidence_reference}} |
