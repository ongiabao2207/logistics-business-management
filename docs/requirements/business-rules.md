# Business Rules

This document defines the business rules that must be preserved by the implementation.

The primary source of truth is `docs/source/QTKD_DATH.pdf`.

Detailed implementation decisions may be taken from `UDPT-03_Report.pdf` only when they do not conflict with the rules defined here.

---

## 1. Contract Rules

### CTR-01 — Editable Contract States

A contract may only be edited when its status is:

- `DRAFT`
- `REVISION_REQUESTED`

Contracts in other states must not be edited directly.

### CTR-02 — Contract Submission Requirements

A contract may only be submitted when:

- the referenced customer is valid;
- the effective period is valid;
- at least one required attachment or required content item is present.

### CTR-03 — Approval Is Mandatory

A contract must not transition directly from `DRAFT` to `APPROVED`.

It must pass through the configured approval workflow.

### CTR-04 — Rejected Contract Handling

A rejected contract must not be automatically modified and resubmitted.

The system must either:

- create a revision; or
- transition the contract back to a revision state according to the designed workflow.

### CTR-05 — Contract Activation

An `APPROVED` contract becomes `ACTIVE` only when its effective start date is reached.

### CTR-06 — Active Contract Deletion

An `ACTIVE` contract must not be deleted.

If the contract is no longer used, it must transition to an appropriate lifecycle state such as:

- `CANCELLED`
- `EXPIRED`

### CTR-07 — Important Changes Require Appendix

Important changes to an `APPROVED` or `ACTIVE` contract must not modify the original contract directly.

A contract appendix must be created instead.

---

## 2. Contract Appendix Rules

Contract appendices belong to Contract Service.

An appendix may change information such as:

- unit prices;
- effective period;
- payment terms;
- registered services.

An appendix must reference an existing contract.

An appendix may have its own approval workflow.

Changes introduced by an appendix only apply to business operations occurring on or after the appendix effective date.

Historical operations before that date must continue using the previous contract or pricing information.

---

## 3. Price List Rules

### PRC-01 — Price Scope

A price list must have a clearly defined scope.

The scope may be associated with:

- a customer;
- a contract;
- a service group;
- another explicitly defined applicable scope.

### PRC-02 — Effective Period

A price list must define an effective period.

`valid_from` must not be later than `valid_to`.

### PRC-03 — No Effective-Date Overlap

Two `EFFECTIVE` price lists must not overlap when they apply to:

- the same scope; and
- the same service type.

### PRC-04 — Price Versioning

When a new price-list version becomes applicable, the previous version must either:

- become `SUPERSEDED`; or
- expire according to its effective date.

### PRC-05 — Historical Price Immutability

A price list that has already been used to generate a payment statement must not be modified directly.

A new price-list version must be created instead.

### PRC-06 — Rejected Price Lists

A `REJECTED` price list may be updated. Saving the revision returns it to `DRAFT`,
after which it may be submitted for approval again.

Only a `DRAFT` price list may be deleted. Price lists in all other states are read-only,
except for the revision of a `REJECTED` price list described above.

---

## 4. Production Rules

Production data represents actual service usage for a customer and contract during a defined period.

Examples include:

- container quantity;
- cargo quantity;
- transportation trips;
- warehouse storage days.

Production records may be modified before the production period is locked.

After the period is locked, production data must not be modified unless the user has an explicitly permitted exceptional authorization.

Only confirmed or reconciled production data may be used as input for payment calculation.

---

## 5. Payment Rules

### PAY-01 — Valid Contract and Price Required

A payment statement may only be created when:

- the contract is valid for the payment period; and
- an applicable price list exists for the calculation period.

### PAY-02 — Production Period Validation

Production data used in a payment statement must:

- belong to the payment period; and
- have been confirmed or reconciled according to the production workflow.

### PAY-03 — Unit Price Snapshot

A payment statement must store the unit price used at calculation time.

Historical payment amounts must not change when a newer price-list version is created.

### PAY-04 — Payment Submission Validation

A payment statement must not be submitted when:

- its total amount is negative; or
- required service lines are missing.

### PAY-05 — Approved and Signed Payments Are Immutable

An `APPROVED` or `SIGNED` payment statement must not be edited directly.

Corrections must use:

- a payment adjustment record; or
- another explicitly defined cancellation/correction workflow.

### PAY-06 — Approval Before E-Sign

A payment statement may only be sent for electronic signature after internal approval has completed successfully.

### PAY-07 — Failed or Cancelled Signing

If electronic signing fails or is cancelled, the signing state must clearly indicate that further action is required.

The system must allow the signing process to be retried when appropriate.

---

## 6. Approval Rules

Approval is handled directly by the service that owns each business document. The standalone Approval Service is not used.

### APR-01 — Reviewer Authorization

Users with `ROLE_LEGAL` or `ROLE_DIRECTOR` may:

- approve;
- reject;
- request revision.

The owning service validates the document is currently in a reviewable state.

### APR-02 — Approval Step Ordering

The system must not allow:

- skipping approval steps;
- approving a step that has already been completed.

### APR-03 — Approval Comments

A reason or comment must be provided for:

- `REJECT`;
- `REQUEST_REVISION`.

### APR-04 — Rejection Handling

When an approval step is rejected, the document must either:

- transition to `REJECTED`; or
- return to a revision state according to the configured workflow.

### APR-05 — Final Approval

When the last configured approval step succeeds:

- the document becomes `APPROVED`;
- subsequent events such as electronic-signing initiation may be triggered.

---

## 7. Electronic Signature Rules

### APR-06 — Asynchronous E-Sign

Electronic signing may be processed asynchronously.

The signing provider may:

1. accept a signing request;
2. process it later;
3. return the result using callback or webhook communication.

The system must maintain the corresponding signing state.

Typical states may include:

- `WAITING_FOR_SIGNATURE`
- `PROCESSING`
- `SIGNED`
- `FAILED`
- `CANCELLED`

Approval status and signing status must remain conceptually separate.

### APR-07 — External Failure Isolation

Temporary failures in:

- Notification Service;
- E-Sign integration;

must not invalidate already completed core business transactions.

The system must support retry or a pending-processing state.

---

## 8. Notification Rules

Notification Service receives asynchronous business events through RabbitMQ.

Core business services must not depend on successful notification delivery to complete their own transaction.

Notifications include events such as:

- document awaiting approval;
- document rejected;
- document approved;
- price list approved;
- electronic signing completed;
- contract approaching expiration;
- price list approaching expiration.

Users must be able to:

- view their notifications;
- see unread status;
- mark notifications as read.

Notification delivery failures must support retry.

---

## 9. Audit Rules

Audit Log Service records significant system and business actions.

Audit records should preserve information including:

- who performed the action;
- when the action occurred;
- the action performed;
- the affected entity;
- previous state;
- resulting state;
- relevant comments or reasons.

Audit history must remain independent from the entity's current display state.

Historical audit information must not disappear simply because the underlying entity later changes.

Audit Log Service is distinct from application/runtime logging.

---

## 10. Idempotency and Concurrency Rules

### Double Submit

Repeated submission of the same document must not create multiple workflow instances.

Possible implementation mechanisms include:

- `Idempotency-Key`;
- database unique constraints;
- equivalent idempotency controls.

### Concurrent Approval

Two concurrent approval requests must not complete the same approval step twice.

Possible mechanisms include:

- database transactions;
- row-level locking;
- optimistic locking.

Only one competing request may successfully complete the approval step.

---

## 11. Event Reliability

A database state change and its corresponding business event must not become inconsistent due to event loss.

The implementation should provide a reliable event-publication mechanism such as:

- Outbox Pattern; or
- another documented retry/reliability mechanism.

Notification or Audit consumer failures must not roll back an already completed core business transaction.

---

## 12. Contextual Authorization

Authorization must consider business context in addition to user roles.

For example:

A manager must not approve an approval step merely because the user has the `MANAGER` role.

The user must also be the assignee of the current step.

---

## 13. Historical Data Consistency

Historical business documents must preserve the values used when they were created.

In particular:

- Payment Service stores a snapshot of the unit price used during calculation.
- A later price-list version must not change previous payment statements.
- An appendix effective from a future date must not affect transactions before that date.
- Audit records retain historical action/state information.

---

## 14. Rule Priority

When implementation details conflict with these rules:

1. follow `QTKD_DATH.pdf`;
2. use the approved design decisions in `UDPT-03_Report.pdf` when they do not conflict with the assignment;
3. do not silently invent a new business rule;
4. ask for clarification before changing an established rule.
