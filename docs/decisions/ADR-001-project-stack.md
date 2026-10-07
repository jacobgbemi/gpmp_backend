# ADR-001: Project Technology Stack

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

GlintPM Private is intended to provide a project-controls platform for project-based organizations. It needs a maintainable web architecture supporting project data, planning and scheduling, progress, cost, reporting, permissions, auditability, integrations, and future automation/AI capabilities.

## Decision

Use a three-tier web application architecture based on:

- **Frontend:** React
- **Backend:** Django with an API layer
- **Database:** PostgreSQL

The architecture should separate presentation, API, business logic, and persistence responsibilities.

```text
User → React Frontend → Django API → Business Services → Django ORM → PostgreSQL
```

External integrations and AI services should be isolated behind explicit service/integration boundaries.

## Rationale

React is suitable for dashboards, forms, reports, planning interfaces, and reusable interactive components.

Django provides mature support for authentication, security, relational models, migrations, transactions, administration, APIs, and testing.

PostgreSQL is well suited to the highly relational and transaction-sensitive nature of project-controls data.

## Consequences

### Positive

- Clear frontend/backend separation.
- Strong relational data integrity.
- Mature ecosystem and tooling.
- Good foundation for enterprise project data.
- Easier integration with scheduling, ERP, reporting, and AI services.

### Negative

- Separate frontend/backend deployment adds complexity.
- API contracts must be maintained.
- Poor query design can cause performance problems.
- Architectural discipline is required.

## Alternatives considered

### Full-stack JavaScript

Not selected because Django is a strong fit for the relational, business-rule-heavy backend.

### Django-rendered frontend

Not selected as the primary architecture because the product is expected to contain rich interactive dashboards and workflows.

### NoSQL-first database

Not selected because the core domain is relationship-heavy and requires strong transactional consistency.

## Implementation notes

This ADR records the architectural decision, not proof that every component is already implemented. Repository code, dependencies, configuration, and tests remain the implementation source of truth.

## Related decisions

- ADR-002: Database Choice
- ADR-003: Authentication Strategy
- ADR-004: API Design
- ADR-005: Multi-Tenancy
- ADR-006: Audit Trail
