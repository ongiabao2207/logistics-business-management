# Business Scenarios

This document defines acceptance-level business scenarios derived from `docs/source/Data-sample.pdf`.

These scenarios should be used as references for:

- acceptance tests;
- integration tests;
- manual demonstrations;
- regression tests.

---

## SC-01 — Submit Contract Without Required Attachment

### Scenario

A user creates a contract but does not attach the required document/content.

### Expected Result

The contract must not be submitted.

### Related Rule

`CTR-02`

### Suggested Acceptance Check

Given:

- a valid customer;
- a valid contract effective period;
- no required attachment;

When the user submits the contract,

Then:

- submission is rejected;
- no approval workflow is created;
- the contract remains in an editable state.

---

## SC-02 — Overlapping Price Lists

### Scenario

A user creates two price lists whose effective periods overlap for the same applicable scope and service type.

### Expected Result

The system reports an effective-period conflict.

The second conflicting price list must not become effective.

### Related Rule

`PRC-03`

### Suggested Acceptance Check

Given an existing effective price:

`01/08/2026 -> 31/12/2026`

When another price for the same scope/service is created with:

`01/10/2026 -> 31/01/2027`

Then the system rejects the conflicting effective period.

---

## SC-03 — Create Payment for Expired Contract

### Scenario

A user attempts to create a payment statement for a period in which the referenced contract has already expired.

### Expected Result

The operation is not allowed.

### Related Rule

`PAY-01`

### Suggested Acceptance Check

Given:

- contract `valid_to` is earlier than the payment period;

When Payment Service attempts to generate the payment statement,

Then:

- payment creation is rejected;
- no payment statement is finalized;
- no approval workflow is created.

---

## SC-04 — Change Price After Payment Is Issued

### Scenario

A price list is changed after it has already been used to generate a payment statement.

### Expected Result

The existing payment statement must remain unchanged.

### Related Rules

- `PRC-05`
- `PAY-03`

### Suggested Acceptance Check

Given:

- Payment A was calculated using unit price `120000`;

When:

- a new price version changes the unit price to `150000`;

Then:

- Payment A still stores and displays `120000`;
- future applicable payments may use `150000`.

---

## SC-05 — Concurrent Approval

### Scenario

Two approval requests attempt to approve the same current approval step at approximately the same time.

### Expected Result

Only one request succeeds.

### Related Rules

- `APR-02`
- Concurrent Approval rule

### Suggested Acceptance Check

Given one pending approval step,

When two valid requests attempt to approve it concurrently,

Then:

- exactly one request completes the step;
- the other request is rejected as already processed or conflicting;
- only one approval-history record represents completion of the step.

---

## SC-06 — Electronic Signature Failure

### Scenario

An electronic signing request ends with a `FAILED` result.

### Expected Result

The system allows the signing operation to be retried.

### Related Rules

- `PAY-07`
- `APR-06`
- `APR-07`

### Suggested Acceptance Check

Given:

- the document has completed internal approval;
- a signing session exists;

When the signing provider returns `FAILED`,

Then:

- the signing session records the failure;
- the business document remains intact;
- the system allows an authorized retry;
- a new signing attempt can be initiated according to the signing workflow.

---

## SC-07 — Notification Service Failure

### Scenario

Notification Service fails while another business operation has already succeeded.

### Expected Result

Notification delivery is retried.

The primary business transaction must not fail.

### Related Rule

`APR-07`

### Suggested Acceptance Check

Given:

- a contract has been successfully submitted or approved;

When:

- the corresponding notification event cannot be processed;

Then:

- the contract/approval transaction remains committed;
- the notification is recorded as pending/failed as appropriate;
- retry is possible;
- the business transaction is not rolled back.

---

## SC-08 — Wrong Approval Assignee

### Scenario

A manager attempts to approve an approval step that is assigned to another user.

### Expected Result

The approval request is rejected.

### Related Rule

`APR-01`

### Suggested Acceptance Check

Given:

- user A has role `MANAGER`;
- the current step is assigned to user B;

When user A submits an `APPROVE` action,

Then:

- the action is rejected;
- the current approval step remains unchanged;
- no successful approval history entry is created for user A.

---

## SC-09 — Repeated Submit

### Scenario

A user submits the same document multiple times.

### Expected Result

Only one workflow instance is created.

### Related Rule

Double Submit / Idempotency rule.

### Suggested Acceptance Check

Given one contract in a submit-ready state,

When multiple equivalent submit requests are received,

Then:

- only one approval workflow instance exists;
- duplicate requests do not create duplicate workflow instances;
- the resulting document state remains consistent.

---

## SC-10 — Appendix Effective Date

### Scenario

An appendix becomes effective on `01/10`, but the system calculates a transaction for September.

### Expected Result

The September transaction uses the old information/price.

### Related Rules

- contract appendix effective-date rule;
- historical data consistency.

### Suggested Acceptance Check

Given:

- original storage price: `120000`;
- appendix changes storage price to `150000`;
- appendix effective date: `01/10/2026`;

When calculating September 2026,

Then:

- the applied price is `120000`.

When calculating an applicable period on or after `01/10/2026`,

Then:

- the new applicable price may be `150000`.

---

# Acceptance Test Mapping

| Scenario | Primary Area | Main Rule |
|---|---|---|
| SC-01 | Contract | CTR-02 |
| SC-02 | Price | PRC-03 |
| SC-03 | Payment | PAY-01 |
| SC-04 | Price / Payment | PRC-05, PAY-03 |
| SC-05 | Approval | APR-02, concurrency |
| SC-06 | E-Sign | PAY-07, APR-06 |
| SC-07 | Notification | APR-07 |
| SC-08 | Approval | APR-01 |
| SC-09 | Approval / Submission | Idempotency |
| SC-10 | Contract Appendix / Price | Effective-date consistency |

---

# Testing Guidance

These scenarios describe expected observable behavior rather than internal implementation.

Tests should verify the business outcome without depending unnecessarily on implementation details.

Recommended test locations:

```text
tests/
└── acceptance/
    ├── test_sc_01_contract_attachment.py
    ├── test_sc_02_price_overlap.py
    ├── test_sc_03_expired_contract.py
    ├── test_sc_04_price_immutability.py
    ├── test_sc_05_concurrent_approval.py
    ├── test_sc_06_esign_retry.py
    ├── test_sc_07_notification_failure.py
    ├── test_sc_08_wrong_assignee.py
    ├── test_sc_09_idempotent_submit.py
    └── test_sc_10_appendix_effective_date.py
```