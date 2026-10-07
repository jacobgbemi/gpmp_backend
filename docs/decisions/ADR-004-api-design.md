# ADR-004: API Design

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

GlintPM Private uses a separate React frontend and Django backend. The API is therefore the contract between the client and server.

The API must support predictable resources, validation, authorization, errors, pagination, and future integrations.

## Decision

Use a **versionable REST-oriented HTTP API**.

The API should expose business resources rather than database implementation details.

Conceptual resource groups:

```text
/api/
├── auth/
├── users/
├── organizations/
├── projects/
├── schedules/
├── baselines/
├── progress/
├── costs/
├── risks/
├── issues/
├── changes/
├── reports/
└── audit/
```

The actual endpoint list is determined by the implementation.

## API principles

### Resource-oriented design

Prefer patterns such as:

```text
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}/
PATCH  /api/projects/{id}/
DELETE /api/projects/{id}/
```

Business actions that do not map naturally to CRUD may use explicit action endpoints.

### Validation

All untrusted input must be validated on the server. Client-side validation is for user experience, not security.

### Authorization

Every protected operation must enforce authorization server-side.

### Consistent errors

A predictable error structure should be used, for example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "fields": {}
  }
}
```

## HTTP status conventions

Typical conventions include:

- `200` successful retrieval/update
- `201` successful creation
- `204` successful operation with no body
- `400` invalid request
- `401` authentication required/failed
- `403` authenticated but not permitted
- `404` resource unavailable
- `409` state/version conflict
- `429` rate limit exceeded
- `500` unexpected server failure

## Pagination

Collection endpoints should use pagination when result sets can become large.

## Idempotency

Retry-prone operations such as imports, integrations, webhooks, and asynchronous jobs should use an appropriate idempotency strategy where duplicate processing would be harmful.

## Versioning

Breaking API changes should be planned. Where compatibility requires it, use an explicit version such as:

```text
/api/v1/
```

## Security

Protected endpoints must apply authentication, authorization, input validation, secure transport, suitable rate limiting, safe error responses, and audit logging for sensitive actions.

## Consequences

### Positive

- Clear frontend/backend contract.
- Easier external integrations.
- Consistent error handling.
- Testable behavior.
- Future mobile/third-party clients can reuse the backend.

### Negative

- API contracts require maintenance.
- Breaking changes require migration planning.
- Poor endpoint design can couple clients to internal structures.

## Alternatives considered

### GraphQL-first

Not selected for the initial architecture because REST is simpler and fits the resource-oriented domain well.

### Direct database access from frontend

Rejected for security, maintainability, and business-rule reasons.

## Implementation notes

The actual API framework, serializers, endpoint paths, authentication method, and versioning approach must be verified from the repository.
