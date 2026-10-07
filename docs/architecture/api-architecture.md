# GlintPM Private — API Architecture

## Purpose
Defines the intended API architecture between the frontend and backend.

## Principles
- Consistent resource design
- Explicit contracts
- Authentication
- Authorization
- Validation
- Predictable errors
- Pagination
- Idempotency where required
- Traceability

## Conceptual API Structure

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

Actual endpoints must be verified.

## Resource Pattern

```text
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}/
PATCH  /api/projects/{id}/
DELETE /api/projects/{id}/
```

## Request Lifecycle

```text
Request → Authentication → Authorization → Validation
→ Business Logic → Database → Serialization → Response
```

## Validation
Validate required fields, types, relationships, state transitions, and business constraints.

## Status Codes
Use consistent semantics such as:
- `200` successful retrieval/update
- `201` created
- `204` successful no-content operation
- `400` invalid request
- `401` unauthenticated
- `403` forbidden
- `404` not found
- `409` conflict
- `500` unexpected server failure

## Pagination
Large collections should support pagination.

## Idempotency
Operations susceptible to duplicate creation after retries should use appropriate idempotency controls.

## Error Contract
A consistent structure is preferred, for example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "fields": {}
  }
}
```

The actual implementation defines the canonical format.

## Testing
Test authentication, authorization, validation, success/failure paths, database effects, response structures, and edge cases.

## Verification Status
Actual endpoints, serializers, response formats, and versioning must be verified against the repository.
