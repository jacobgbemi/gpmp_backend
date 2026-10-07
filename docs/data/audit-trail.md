# Data Audit Trail

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

This document defines data-level requirements for recording historical changes and important events. The broader architectural decision is documented in `docs/decisions/ADR-006-audit-trail.md`.

## Audit objectives

The audit system should answer who acted, what happened, when, which organization was involved, which resource was affected, what changed, and why where required.

## Priority events

- authentication/security events
- membership and permission changes
- project creation/archive
- baseline creation/approval
- significant schedule updates
- progress submissions
- cost/forecast changes
- risk changes
- change requests
- approvals/rejections
- important configuration changes
- imports/exports

## Conceptual event model

```text
AuditEvent
├── id
├── organization
├── actor
├── event_type
├── action
├── resource_type
├── resource_id
├── occurred_at
├── correlation_id
├── change_summary
└── metadata
```

## Before/after data

Capture before/after values where they provide meaningful accountability. Avoid storing entire records for every event because of storage, privacy, and noise concerns.

## Immutability

Normal workflows should not permit users to edit or delete audit records. Controlled retention operations must themselves be audited.

## Transactions

Where a business operation and audit event are one atomic operation, commit them together. Asynchronous jobs need traceable completion, failure, and retry behavior.

## Tenant context

Tenant-owned audit events must retain organization context and enforce organization boundaries when queried.

## Sensitive data

Never store passwords, authentication tokens, API keys, secrets, or unnecessary sensitive personal information in audit records.

## Access and retention

Audit data should be permission-controlled. Retention must reflect customer, legal, compliance, security, and operational requirements.

## Implementation note

The physical audit schema, event generation mechanism, event catalog, retention policy, and access controls must be verified against the repository.
