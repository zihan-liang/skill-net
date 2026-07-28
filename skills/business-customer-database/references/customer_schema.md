# Customer Database Schema

The tool implements a local SQLite demonstration. Every write requires an actor, business purpose, evidence reference, and explicit confirmation. `audit_log` is append-only.

## Entities

| Entity type | Table | Stable ID | Parent links | Minimum purpose |
|---|---|---|---|---|
| `customer` | `customers` | `customer_id` | none | Basic legal/display identity, segment, region, owner, status |
| `contact` | `contacts` | `contact_id` | customer | Minimum business contact and contact basis |
| `requirement` | `customer_requirements` | `requirement_id` | customer | Versioned customer need summary and evidence |
| `communication` | `communication_records` | `communication_id` | customer, contact, requirement | Dated channel summary and restricted evidence reference |
| `quotation` | `quotation_records` | `quotation_id` | customer | Opportunity, quotation number/version, currency, amount, validity, status |
| `contract` | `contract_records` | `contract_id` | customer, quotation | Contract reference/version/digest, dates, status, execution evidence |
| `project_progress` | `project_progress` | `progress_id` | customer, contract | Project/reporting date, completion, status, evidence |
| `payment` | `payment_records` | `payment_id` | customer, contract | Amount/currency, due/received dates, status, evidence |
| `renewal` | `renewal_records` | `renewal_id` | customer, contract | Renewal date, proposed value/currency, status, evidence |

## Relationship Rules

- Child customer IDs must reference an existing customer.
- Communication contact and requirement records must belong to the same customer.
- A contract customer must match its quotation customer.
- Project progress, payment, and renewal customers must match their contract customer.
- Business email is unique per customer, quotation number/version is unique per customer, and contract reference is globally unique, using case-insensitive comparison.

## Data Rules

- Currency uses a three-letter code; money uses decimal strings.
- Dates use `YYYY-MM-DD`; communication and received timestamps include a timezone.
- Contract documents use `sha256:<64 hexadecimal characters>` references, not full files.
- Completion is 0–100. A received payment requires a received timestamp.
- Corrections update the stable record while appending before/after audit JSON.

## Excluded Data

Never store passwords, tokens, identity documents, bank accounts, payment-card data, recordings, message bodies, full proposals/contracts, binary attachments, or unrelated personal data. Store only restricted references when evidence is required.
