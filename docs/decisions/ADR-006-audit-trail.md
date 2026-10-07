# ADR-006: Audit Trail

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

Project-controls systems manage information that can affect schedules, budgets, forecasts, commitments, approvals, and management decisions.

For important records, users need to know what changed, who changed it, when it changed, and, where appropriate, why.

## Decision

Implement an **application-level audit trail for security-sensitive and business-critical events**, stored persistently and associated with the relevant organization and user where applicable.

Audit records should be append-oriented. Normal users must not be able to rewrite historical audit evidence.

## Events to audit

### Authentication/security

- login
- logout where useful
- failed authentication
- password reset
- permission/security changes
- account activation/deactivation

### Project controls

- project creation/archival
- baseline creation or approval
- significant schedule updates
- progress submissions
- cost/forecast changes
- risk status changes
- change requests
- approvals/rejections

### Administration

- organization changes
- user membership changes
- role/permission changes
- important configuration changes

The event catalog should evolve with the product.

## Audit record structure

A useful event can capture:

```text
Audit Event
├── event type
├── timestamp
├── actor/user
├── organization/tenant
├── affected resource
├── resource identifier
├── action
├── previous state or change summary
├── new state or change summary
├── reason/comment where required
├── request/correlation identifier
└── metadata
```

Not every event requires complete before/after snapshots.

## Immutability

Normal application flows should not permit users to edit or delete audit records.

If retention rules require deletion, it should occur through a controlled administrative process and itself be auditable.

## Audit vs application history

An `updated_at` field is not an audit trail.

The audit trail should answer:

- Who acted?
- What happened?
- When?
- Which organization?
- Which record?
- What changed?
- What relevant reason/context existed?

## Privacy and sensitive data

Do not store passwords, authentication tokens, API secrets, or unnecessary sensitive personal information in audit records.

## Transactions

Where an auditable business operation changes authoritative data, the audit event should be written in the same transaction when appropriate.

Asynchronous jobs need explicit handling for completion, failure, and retries.

## Access

Audit data should be permission-controlled and may be limited to organization administrators, project leadership, project-controls leadership, or compliance personnel.

## Retention

Retention should be based on customer requirements, legal obligations, security needs, and storage cost. Automated deletion should not be introduced without a documented policy.

## Alternatives considered

### Application logs only

Rejected. Operational logs are not a sufficient business audit record.

### Database timestamps only

Rejected. Timestamps cannot explain who acted or what changed.

### Full event sourcing

Not selected initially because it adds significant complexity that is not necessary for every domain operation.

## Consequences

### Positive

- Improved accountability.
- Better investigation of disputes and unexpected changes.
- Stronger governance for project controls.
- Useful evidence for approvals and decisions.

### Negative

- Additional storage.
- Additional implementation/testing effort.
- Retention requires governance.
- Poorly designed events can create excessive noise.

## Implementation notes

The actual audit model, implementation mechanism, event catalog, retention policy, and access controls must be verified against the repository.
