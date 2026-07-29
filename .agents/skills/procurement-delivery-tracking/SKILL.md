---
name: procurement-delivery-tracking
description: Use when a released purchase order needs supplier confirmation, expected delivery, logistics or service milestones, delay, exception, and expediting records; not for accepting delivery.
---

# Procurement Delivery Tracking

## Overview

Track an issued PO from supplier acknowledgement through delivery readiness while keeping observed progress separate from receipt and acceptance.

**中文摘要：** 跟踪订单确认、预计交付、物流或服务里程碑、延期、异常和催交记录；不负责收货或验收。

## Required Inputs

- Released PO and contract IDs/versions, supplier acknowledgement, lines, delivery terms, and owners
- Expected ship/delivery dates, logistics or service milestones, locations, dependencies, contacts, and source evidence
- Expediting/escalation policy, exception authority, reporting date, and communication route

## Workflow

1. Read `assets/delivery_tracking_template.md`; assign tracking/milestone IDs.
2. Verify release and supplier acknowledgement evidence before recording confirmed dates.
3. Track each PO line or service milestone with planned, supplier-reported, and evidenced status separately.
4. Record dispatch, logistics/service progress, forecast date, delay, dependency, and exception evidence.
5. Calculate overdue and at-risk milestones without inventing location or completion.
6. Draft expediting, recovery, and escalation actions with owners and due dates.
7. Route supplier communication and schedule changes to authorized humans.

## Output Contract

Return PO/tracking/supplier IDs, reporting date, line/milestone statuses, acknowledgements, expected/forecast dates, logistics/service evidence, delays, exceptions, expediting actions, owners, and `delivery_status`.

## SkillNet Relationships

- Part of `procurement-agent`.
- Enhances `procurement-supplier-evaluation` when `delivery_history_available`.
- Follows `procurement-purchase-order`.
- Precedes `business-acceptance` when `business_service_purchase`.
- Precedes `technology-test-acceptance` when `technology_purchase`.

## Approval Controls

- Use stable IDs, minimum fields, restricted evidence references, source timestamps, actor/purpose, and append-only status history.
- Do not invent acknowledgement, shipment, location, milestone completion, supplier response, or revised commitment.
- Human approval is required for supplier messages, schedule/contract changes, expedite costs, cancellations, and exception commitments.

## Exception Handling

- Escalate missing acknowledgement, overdue milestones, inconsistent tracking, lost/damaged shipment indicators, or service dependency failure.
- Preserve the original promise and all revisions; do not overwrite delays or treat a supplier forecast as confirmed receipt.

## Handoff

Pass the PO lines, arrival/service evidence, tracking timeline, exceptions, open corrective actions, and receiving instructions to `procurement-delivery-acceptance`.

## Example

Track a 20-laptop order from acknowledgement through dispatch, flag a two-day delay, and draft an approved-channel expedite request without marking receipt.

## Common Mistakes

- Treating supplier-reported shipment as delivery
- Hiding revised dates or delays
- Combining tracking with acceptance
