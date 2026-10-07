# ADR-002: Database Choice

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

GlintPM Private will store organization, user, project, scheduling, cost, progress, risk, change, reporting, and audit information. These entities have strong relationships and require reliable transactions and historical traceability.

## Decision

Use **PostgreSQL** as the primary relational database.

Django ORM should normally be used at the application layer. Direct SQL should only be introduced where there is a justified requirement.

## Rationale

PostgreSQL provides:

- ACID transactions
- foreign keys and relational integrity
- unique and check constraints
- mature indexing
- strong aggregation and reporting
- JSON support where appropriate
- mature backup/recovery tooling
- suitable scalability

## Data integrity principles

Important rules should be enforced at the application layer and, where appropriate, at the database layer using:

- foreign keys
- unique constraints
- check constraints
- non-null requirements
- appropriate data types

The database should not be treated as a passive storage bucket.

## Financial and project-control data

Use exact numeric/decimal representations where financial precision matters.

Currency should be explicit. Timestamps should follow a consistent timezone strategy. Reporting periods and project calendars should be modeled explicitly where they affect calculations.

## Transactions

Multi-record operations should use transactions when atomicity is required, including baseline approval, progress updates, controlled changes, and batch imports.

## Migrations and indexes

All schema changes should be version-controlled through migrations.

Indexes should be based on real query patterns and measured performance needs rather than added indiscriminately.

## Alternatives considered

### MySQL

A capable relational database, but PostgreSQL is preferred for the expected combination of integrity, querying, extensibility, and Django support.

### MongoDB

Not selected because the core domain is strongly relational.

### SQLite

Useful for lightweight development/testing, but not the primary production database.

## Consequences

### Positive

- Strong consistency and integrity.
- Excellent fit for relational project data.
- Strong reporting/query capabilities.
- Good long-term foundation.

### Negative

- Requires database administration and backup planning.
- Poor queries can still cause performance issues.
- Large analytical workloads may eventually need specialized reporting strategies.

## Implementation notes

The actual schema must be derived from repository models and migrations. This ADR establishes PostgreSQL as the target decision.
