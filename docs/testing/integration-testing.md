# Integration Testing

**Status:** Testing baseline

## Purpose

Integration tests verify that application components work correctly together, including Django application code, ORM/database behavior, authentication, permissions, and external boundaries.

## Key Integration Areas

- Django views and services with the ORM.
- Database constraints and transactions.
- Authentication middleware/session or token behavior.
- Organization/tenant scoping.
- Permission enforcement.
- File import/export workflows.
- Report generation.
- Background jobs, if present.
- External service adapters, where applicable.

## Database Tests

Integration tests should verify:

- Foreign-key relationships.
- Unique constraints.
- Required fields.
- Transaction rollback behavior.
- Cascading or protected deletes.
- Tenant isolation.
- Concurrent update assumptions where relevant.

## Transaction Integrity

For operations that modify multiple related records, tests should verify that partial writes are not left behind when a later operation fails.

## External Dependencies

External systems should normally be replaced with controlled test doubles or dedicated test environments. Tests must not send unintended production requests.

## Implementation Note

Actual database configuration, test database behavior, integration fixtures, and external integrations must be verified against the repository.
