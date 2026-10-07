# GlintPM Private — Backend Architecture

## Purpose
The intended backend direction is Django-based with an API supporting the React frontend. Exact implementation must be verified from the repository.

## Responsibilities
- Authentication
- Authorization
- Validation
- Business rules
- Project-control calculations
- Database persistence
- Transactions
- Audit events
- API responses
- External integrations
- Server-side security

## Conceptual Architecture

```text
HTTP Request
 ↓
URL Routing
 ↓
API View / Controller
 ↓
Authentication
 ↓
Authorization
 ↓
Validation / Serializer
 ↓
Business Service
 ↓
Domain / ORM Models
 ↓
Database
```

## Suggested Django Structure

```text
backend/
├── config/
├── apps/
│   ├── accounts/
│   ├── organizations/
│   ├── projects/
│   ├── scheduling/
│   ├── costs/
│   ├── progress/
│   ├── risks/
│   ├── changes/
│   ├── reporting/
│   └── audit/
├── tests/
└── manage.py
```

This is a proposal, not a description of the current repository.

## Models
Models should represent persistent entities, relationships, constraints, and appropriate validation. Complex workflows should not automatically be placed inside models.

## Serializers / Schemas
Define input validation, output representation, field exposure, and relationships.

## Business Services
Complex operations such as baseline establishment, progress processing, calculations, approvals, and report generation may be placed in explicit services/domain functions.

## Transactions
Multi-record operations that must remain consistent should use appropriate transaction boundaries.

## Error Handling
Provide consistent handling for validation, authentication, authorization, missing resources, conflicts, and unexpected errors without exposing sensitive internals.

## Background Processing
Long-running work such as large imports, report generation, synchronization, notifications, or AI processing should be asynchronous where justified.

## Auditability
Business-critical actions should record appropriate actor, entity, timestamp, action, and relevant change information.

## Testing
Critical backend tests should cover business rules, APIs, authentication, authorization, database integrity, calculations, and failure cases.

## Verification Status
Actual Django apps, libraries, service boundaries, and implementation details must be verified against the repository.
