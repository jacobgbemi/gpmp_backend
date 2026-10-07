# GlintPM Private — Database Architecture

## Purpose
The database is a critical component because project-control information must remain consistent, traceable, and reliable. PostgreSQL with Django ORM is the intended direction, subject to repository verification.

## Principles
- Relational integrity
- Explicit relationships
- Appropriate constraints
- Transactional consistency
- Auditability
- Version-controlled migrations
- Evidence-based indexing
- Clear ownership
- No unexplained duplication

## Conceptual Domain Model

```text
Organization
    ↓
Project
    ├── Schedule / Planning
    ├── Baseline
    ├── Progress
    ├── Costs
    ├── Risks
    ├── Issues
    ├── Changes
    ├── Actions
    ├── Decisions
    └── Reports
```

This is conceptual and does not claim that all entities currently exist.

## Entity Design
Important entities should have stable identifiers, appropriate types, ownership/context, timestamps where appropriate, relationships, and constraints.

## Relationships
Use explicit relational keys rather than important relationships stored only as text.

## Constraints
Database constraints should protect important invariants such as unique project references, valid foreign keys, valid statuses, and appropriate ownership.

## Transactions
Use atomic transactions for multi-step operations that must not leave partial state.

## Audit Data
Distinguish business audit records, technical logs, and security events.

## Financial Data
Use exact numeric types for financial values where precision matters. Currency should be explicit when multi-currency operation is possible.

## Date and Time
Define time zones, reporting periods, project calendars, baseline dates, actual dates, and forecast dates explicitly.

## Migrations
Schema changes must use version-controlled migrations and should be tested before production application.

## Indexing
Create indexes based on actual query patterns, especially for frequent filters, relationships, reporting periods, and status fields.

## Backup and Recovery
Production data should have automated backups, documented recovery procedures, and tested restoration.

## Verification Status
Actual models, fields, relationships, indexes, constraints, and migrations must be derived from the current repository.
