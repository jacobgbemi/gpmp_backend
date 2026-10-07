# Data Integrity

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

Data integrity ensures stored information remains accurate, consistent, complete, and trustworthy. This is critical because project-controls data can influence time, cost, risk, and delivery decisions.

## Principles

1. One authoritative source for each core fact.
2. Explicit relationships.
3. Database constraints for structural rules.
4. Server-side business rules.
5. Atomic transactions for related changes.
6. Controlled state transitions.
7. Tenant isolation.
8. Historical traceability.
9. Controlled imports.
10. Tested calculations.

## Referential integrity

Use foreign keys and appropriate deletion behavior to prevent orphaned records.

## Uniqueness

Business identifiers should be unique within the appropriate scope, such as project code within an organization if that matches business rules.

## State integrity

Lifecycle states should have explicit transitions. Approved records should not silently return to draft through ordinary updates.

## Transactions

Use transactions when partial completion would create inconsistent data, such as baseline creation plus approval plus audit records.

## Concurrency

Where simultaneous editing is possible, use appropriate optimistic locking/version checks, database locking, unique constraints, or conflict detection.

## Calculation integrity

Derived metrics should identify source inputs and calculation definitions. Critical calculations should have automated tests.

## Import integrity

Bulk imports should validate before committing changes:

```text
Upload → Parse → Validate → Preview → Approve → Commit → Audit
```

## Tenant integrity

Records from one organization must not be linked to records belonging to another organization unless explicitly permitted.

## Recovery

Production operations should define backup frequency, retention, restore testing, recovery objectives, and migration recovery procedures.
