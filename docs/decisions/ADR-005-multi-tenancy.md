# ADR-005: Multi-Tenancy

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

GlintPM Private is intended to support multiple project-based organizations. Their users, projects, schedules, financial information, and reports must remain isolated.

Tenant isolation is a core security requirement.

## Decision

Use **organization-scoped multi-tenancy**, with the organization represented explicitly in the domain model and enforced by the backend.

The initial baseline is a **shared application and shared PostgreSQL database with logical tenant isolation**.

```text
Platform
├── Organization A
│   ├── Users
│   ├── Projects
│   └── Project Data
├── Organization B
│   ├── Users
│   ├── Projects
│   └── Project Data
└── Organization C
    ├── Users
    ├── Projects
    └── Project Data
```

## Tenant identification

Tenant context must be established from trusted server-side information.

A client-supplied organization ID is not sufficient proof of membership.

```text
Authenticated User
        ↓
Organization Membership
        ↓
Authorized Tenant Context
        ↓
Resource Query
```

## Data isolation

Tenant-owned records should have an explicit organization relationship directly or through an unambiguous ownership chain.

Queries must apply the correct tenant scope.

## Authorization

Tenant isolation and role authorization are separate controls.

A user belonging to Organization A must not access Organization B simply by changing a URL or resource ID.

## Cross-tenant operations

Cross-tenant access is prohibited by default. Legitimate platform-level operations must be explicitly designed, highly privileged, and audited.

## Imports and exports

Imports and exports must preserve tenant boundaries and verify authorization before processing or producing data.

## Alternatives considered

### Database per organization

Provides strong physical isolation but increases provisioning, migration, and operational complexity.

### Schema per organization

Provides stronger database separation but adds migration and provisioning complexity.

### Shared tables without tenant scoping

Rejected because it creates unacceptable cross-organization data leakage risk.

## Future evolution

The design should leave room for stronger isolation models later, including:

- PostgreSQL row-level security
- separate schemas
- separate databases
- regional data isolation

## Testing requirements

Automated tests should verify that:

- users cannot retrieve another organization's projects
- users cannot modify another organization's records
- foreign resource IDs cannot bypass authorization
- list endpoints do not leak cross-tenant data
- exports respect tenant boundaries
- background jobs preserve tenant context

## Consequences

### Positive

- Efficient initial deployment model.
- Clear organization ownership.
- Supports multiple organizations.
- Allows future stronger isolation.

### Negative

- Tenant filtering must be consistently enforced.
- A missed authorization boundary can cause severe data leakage.
- Background jobs and integrations require careful tenant-context handling.

## Implementation notes

The exact tenancy model, organization membership implementation, database constraints, query patterns, and permissions must be verified against the repository.
