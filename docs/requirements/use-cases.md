# Use Cases

This document summarizes the functional use cases of the Logistics Business Management System.

It describes **what users and the system must be able to do**.

Detailed API design, database design, service communication, and deployment decisions belong under `docs/architecture/` and service-specific documentation.

---

# 1. Actors

## Sales Staff

Main responsibilities:

- manage customers;
- create and manage contracts;
- create contract appendices;
- propose/manage price-related business records;
- submit documents for approval;
- monitor document status.

## Operations Staff

Main responsibilities:

- create production periods;
- record actual production/service usage;
- reconcile production data;
- lock production periods.

## Accounting Staff

Main responsibilities:

- create payment statements;
- validate payment information;
- review payment calculations;
- submit payment documents for approval;
- monitor payment status.

## Legal Staff

Main responsibilities:

- review assigned documents;
- approve;
- reject;
- request revision;
- review contract and appendix content.

## Manager / Director

Main responsibilities:

- process assigned approval steps;
- approve important business documents;
- participate in electronic-signing workflows when assigned.

## System Administrator

Main responsibilities:

- manage users;
- manage roles and permissions;
- configure workflow definitions;
- configure document-related system settings.

## External E-Sign Provider

External system responsible for processing electronic-signing requests and returning their results asynchronously.

---

# 2. Customer Management

## UC-CUS-01 — View and Search Customers

### Primary Actor

Sales Staff

### Goal

View the customer list and search for a particular customer.

### Preconditions

- User is authenticated.
- User has permission to view customer information.

### Main Flow

1. User opens Customer Management.
2. System displays available customers.
3. User enters search/filter criteria.
4. System returns matching customers.
5. User may open customer details.

### Postconditions

No customer data is modified.

---

## UC-CUS-02 — Create Customer

### Primary Actor

Sales Staff

### Goal

Create customer information so the customer can participate in contracts and related business processes.

### Main Flow

1. User collects customer legal/contact information.
2. User enters customer information.
3. System validates required data.
4. System checks uniqueness constraints such as tax code.
5. System creates the customer.
6. Customer becomes available for contract-related operations.

### Expected Result

A valid customer record exists with an appropriate active status.

---

## UC-CUS-03 — Update Customer

### Primary Actor

Sales Staff

### Preconditions

- Customer exists.
- User has update permission.

### Main Flow

1. User selects a customer.
2. System displays current information.
3. User edits permitted fields.
4. System validates the changes.
5. System saves the updated customer information.
6. Relevant audit/event information is generated.

### Postconditions

Customer information is updated while historical business records remain intact.

---

## UC-CUS-04 — Suspend Customer

### Primary Actor

Sales Staff

### Goal

Mark a customer as inactive without deleting historical data.

### Main Flow

1. User selects an active customer.
2. User requests suspension.
3. System changes customer status to `INACTIVE`.

### Postconditions

- Customer remains stored.
- Existing contracts, appendices, payments, and historical records remain available.

---

# 3. Contract Management

## UC-CTR-01 — Create Contract

### Primary Actor

Sales Staff

### Preconditions

- User is authenticated.
- User has contract-management permission.

### Main Flow

1. User selects an existing customer or creates customer information when required.
2. User enters contract information.
3. User defines the contract effective period.
4. User specifies service/payment-related contract information.
5. User attaches required documents/content.
6. System validates the contract.
7. System saves the contract in `DRAFT`.

### Postconditions

A new contract draft exists.

---

## UC-CTR-02 — Edit Contract

### Primary Actor

Sales Staff

### Preconditions

- Contract exists.
- Contract is in `DRAFT` or `REVISION_REQUESTED`.

### Main Flow

1. User selects a contract.
2. System displays current contract information.
3. User modifies permitted information.
4. System validates the update.
5. System saves the changes.

### Alternative Flow

If the contract is not in an editable state, the update is rejected.

### Related Rule

`CTR-01`

---

## UC-CTR-03 — Submit Contract for Approval

### Primary Actor

Sales Staff

### Preconditions

- Contract is in a submit-eligible state.
- Customer is valid.
- Effective dates are valid.
- Required attachment/content exists.

### Main Flow

1. User requests contract submission.
2. System validates submission requirements.
3. System creates or requests an approval workflow instance.
4. Contract transitions to the appropriate submitted/pending-approval state.
5. Relevant events are published.

### Alternative Flow

If validation fails, the contract remains unsubmitted.

### Related Rules

- `CTR-02`
- `CTR-03`
- idempotent submission rule.

---

## UC-CTR-04 — Cancel or End Contract

### Primary Actor

Authorized Business User

### Goal

End use of a contract without deleting an active historical record.

### Expected Result

The contract transitions to an appropriate lifecycle state such as:

- `CANCELLED`;
- `EXPIRED`.

### Related Rule

`CTR-06`

---

# 4. Contract Appendix Management

Contract appendices are owned by Contract Service.

There is no separate Appendix microservice.

## UC-APP-01 — Create Contract Appendix

### Primary Actor

Sales Staff

### Preconditions

- Parent contract exists.
- Proposed change requires an appendix rather than direct contract modification.

### Main Flow

1. User selects the parent contract.
2. User enters appendix information.
3. User defines the effective date.
4. User specifies changed terms.
5. Changes may include:
   - unit price;
   - contract duration;
   - payment terms;
   - service additions or changes.
6. System validates the appendix.
7. System creates the appendix in an initial workflow state.

### Postconditions

The original contract remains unchanged.

---

## UC-APP-02 — Update Contract Appendix

### Primary Actor

Sales Staff

### Preconditions

- Appendix exists.
- Appendix is in an editable state.

### Main Flow

1. User selects the appendix.
2. System displays its current information.
3. User edits permitted fields.
4. System validates the new data.
5. System saves the changes.

### Postconditions

The appendix remains associated with its parent contract.

---

## UC-APP-03 — Submit Appendix for Approval

### Primary Actor

Sales Staff

### Main Flow

1. User submits the appendix.
2. System validates submission requirements.
3. Approval workflow is created according to the applicable configuration.
4. Appendix enters the appropriate pending-approval state.

---

## UC-APP-04 — Apply Effective Appendix

### Trigger

The appendix is approved and its effective date is reached.

### Expected Result

Business operations on or after the effective date use the updated appendix information.

Historical operations before that date continue using the previous information.

---

# 5. Price Management

## UC-PRC-01 — View Services and Price Lists

### Primary Actor

Authorized Business User

### Goal

View available services and price-list versions.

---

## UC-PRC-02 — Create Price List Version

### Primary Actor

Sales/Authorized Business User

### Main Flow

1. User selects the applicable scope.
2. User defines effective dates.
3. User defines service prices.
4. System validates the price list.
5. System checks for conflicting effective periods.
6. System creates a new price-list version.

### Alternative Flow

If an effective-period overlap violates `PRC-03`, creation/effectivation is rejected.

---

## UC-PRC-03 — Submit Price List for Approval

### Primary Actor

Authorized Business User

### Main Flow

1. User submits a valid price list.
2. System creates the configured approval workflow.
3. Price list moves to a pending-approval state.

---

## UC-PRC-04 — Resolve Effective Price

### Primary Consumer

Other business services, especially:

- Contract Service;
- Payment Service.

### Goal

Determine the price applicable to a service and business date.

### Expected Result

The price version effective for the requested scope and date is returned.

Historical versions remain available for historical business records.

---

# 6. Production Management

## UC-PROD-01 — Create Production Period

### Primary Actor

Operations Staff

### Main Flow

1. User selects customer and contract.
2. User defines the production period.
3. System verifies that the contract covers the relevant period.
4. System creates the production period.

### Alternative Flow

If the contract does not cover the period, creation is rejected.

---

## UC-PROD-02 — Record Production

### Primary Actor

Operations Staff

### Main Flow

1. User selects an existing production period.
2. User records actual operational quantities.
3. Quantities may include:
   - containers;
   - transportation trips;
   - storage days;
   - other supported service units.
4. System validates and stores the production records.

---

## UC-PROD-03 — Reconcile Production

### Primary Actor

Operations Staff

### Goal

Compare recorded production data with operational evidence and confirm its correctness.

### Main Flow

1. User reviews recorded quantities.
2. User compares them with operational records.
3. Incorrect values may be corrected while the period remains editable.
4. User confirms the reconciled data.

---

## UC-PROD-04 — Lock Production Period

### Primary Actor

Operations Staff

### Preconditions

Production data has been reviewed/reconciled.

### Main Flow

1. User requests period locking.
2. System validates the period.
3. System marks the period as locked.

### Postconditions

Normal users can no longer modify production values in the locked period.

The data is available as payment-calculation input.

---

# 7. Payment Management

## UC-PAY-01 — Preview Payment Statement

### Primary Actor

Accounting Staff

### Preconditions

- Contract is valid for the payment period.
- Applicable price information exists.
- Production data exists and is eligible for calculation.

### Main Flow

1. User selects customer, contract, and payment period.
2. System obtains the relevant contract information.
3. System obtains applicable production data.
4. System obtains applicable price information.
5. System calculates:
   - quantity;
   - unit price;
   - line amount;
   - tax;
   - total amount.
6. System displays a payment preview.

### Postconditions

No finalized payment statement is required to exist yet.

---

## UC-PAY-02 — Create Payment Statement

### Primary Actor

Accounting Staff

### Main Flow

1. User confirms the payment preview.
2. System creates the payment statement.
3. System stores payment line details.
4. Unit prices are stored as snapshots.
5. Payment history is recorded.

### Related Rule

`PAY-03`

---

## UC-PAY-03 — Submit Payment for Approval

### Primary Actor

Accounting Staff

### Preconditions

The payment statement satisfies submission validation.

### Main Flow

1. User submits the payment statement.
2. System creates the appropriate approval workflow.
3. Payment moves to its configured pending-approval state.

### Alternative Flow

Submission is rejected when required payment data is invalid.

---

## UC-PAY-04 — Adjust Payment

### Primary Actor

Authorized Accounting User

### Preconditions

A payment requiring correction already exists.

### Main Flow

1. User identifies the payment statement.
2. User creates an adjustment record.
3. User specifies adjustment reason/content.
4. Adjustment follows the configured workflow.

### Related Rule

An `APPROVED` or `SIGNED` payment statement must not be edited directly.

---

# 8. Approval Management

Approval workflows are configurable by document type.

Possible approvable documents include:

- contracts;
- contract appendices;
- price lists;
- payment statements.

## UC-APR-01 — View Assigned Approval Tasks

### Primary Actor

Approver

### Main Flow

1. User opens assigned approval tasks.
2. System returns pending steps assigned to the current user.
3. User selects a document to review.

---

## UC-APR-02 — View Approval Detail

### Primary Actor

Approver

### Main Flow

1. User selects an assigned approval instance.
2. System loads the referenced document.
3. System displays:
   - document information;
   - attachments where applicable;
   - current workflow step;
   - previous approval history;
   - comments.

---

## UC-APR-03 — Approve Document

### Primary Actor

Current Step Assignee

### Preconditions

- User is the current assignee.
- Approval step is still pending.
- Previous required steps have completed.

### Main Flow

1. User reviews the document.
2. User selects `APPROVE`.
3. System validates assignment and current step.
4. System records the approval action.
5. System advances to the next configured step.

### Final Step

If this is the last approval step:

- the document becomes `APPROVED`;
- subsequent processes such as E-Sign may begin.

---

## UC-APR-04 — Reject Document

### Primary Actor

Current Step Assignee

### Main Flow

1. User selects `REJECT`.
2. User provides a reason.
3. System records the rejection.
4. Document transitions according to the configured rejection workflow.

---

## UC-APR-05 — Request Revision

### Primary Actor

Current Step Assignee

### Main Flow

1. User selects `REQUEST_REVISION`.
2. User provides revision comments.
3. System records the action.
4. Document moves to the configured revision state.
5. Document owner is notified asynchronously.

---

# 9. Electronic Signature

## UC-SIGN-01 — Start Signing Session

### Trigger

A document requiring signature completes internal approval.

### Preconditions

The related approval workflow is `APPROVED`.

### Main Flow

1. Approval Service creates a signing session.
2. Signing steps/signers are defined.
3. The first signing request is sent to the E-Sign provider.
4. Provider accepts the asynchronous request.
5. Signing state becomes pending/processing.

---

## UC-SIGN-02 — Process Signing Callback

### Primary Actor

External E-Sign Provider

### Main Flow

1. Provider sends a callback/webhook.
2. System validates the callback.
3. System updates the signing step.
4. Signature metadata/result is stored.
5. If another signer remains, the next step becomes available.
6. If all required signing steps are complete, the signing session becomes completed.

### Postconditions

The referenced business document may transition to `SIGNED`.

---

## UC-SIGN-03 — Retry Failed Signing

### Primary Actor

Authorized User

### Preconditions

Previous signing attempt is `FAILED` or otherwise retryable.

### Expected Result

A new signing attempt may be initiated without recreating or corrupting the approved business document.

---

# 10. Notification Management

Notification Service operates asynchronously through RabbitMQ.

## UC-NOT-01 — Receive Business Event

### Trigger

Another service publishes a supported business event.

### Main Flow

1. Notification Service consumes the RabbitMQ event.
2. It determines notification recipients/content.
3. Notification records are created.
4. Delivery is attempted.

### Failure Flow

If delivery fails:

- the core business operation remains successful;
- delivery status records the failure;
- retry is possible.

---

## UC-NOT-02 — View Notifications

### Primary Actor

Authenticated User

### Main Flow

1. User opens notifications.
2. System displays notifications belonging to that user.
3. Unread status is shown.

---

## UC-NOT-03 — Mark Notification as Read

### Primary Actor

Authenticated User

### Main Flow

1. User selects a notification.
2. System updates that user's read status.
3. Relevant audit information is generated.

---

# 11. Audit and Traceability

## UC-AUD-01 — Record Audit Event

### Trigger

A significant business action occurs.

Examples:

- create;
- update;
- submit;
- approve;
- reject;
- request revision;
- signing result;
- notification read.

### Main Flow

1. Audit Log Service receives the relevant audit event.
2. It records:
   - actor;
   - action;
   - entity;
   - timestamp;
   - state before;
   - state after;
   - comments when applicable.

### Postconditions

Historical audit information is preserved independently from the entity's current state.

---

## UC-AUD-02 — View Entity History

### Primary Actor

Authorized User

### Goal

Trace significant historical actions for an entity such as:

- contract;
- price list;
- payment statement;
- signing session.

---

# 12. Authentication and Authorization

## UC-AUTH-01 — Login

### Primary Actor

System User

### Main Flow

1. User submits credentials.
2. Identity Service validates the credentials.
3. A JWT is issued when authentication succeeds.

---

## UC-AUTH-02 — Access Protected Function

### Primary Actor

Authenticated User

### Main Flow

1. User sends a request with JWT.
2. Authentication is validated.
3. The target service evaluates required authorization.
4. Contextual business authorization is applied where required.

### Example

For approval, having the correct role is not sufficient.

The user must also be the current approval-step assignee.

---

# 13. Cross-Use-Case Requirements

The following requirements apply across multiple use cases:

- Business services must preserve service ownership boundaries.
- Approval workflows are configurable by document type.
- Notification processing is asynchronous through RabbitMQ.
- Audit Log Service is the canonical business-audit component.
- Contract appendices are part of Contract Service.
- Historical price/payment information must remain immutable.
- Duplicate submission must not create duplicate workflow instances.
- Concurrent approval must not complete the same step twice.