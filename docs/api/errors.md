# API Errors

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The API should return consistent, safe, and actionable errors across all resources.

## Error structure

Preferred conceptual structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "fields": {"name": ["This field is required."]},
    "request_id": "req-123"
  }
}
```

The exact production schema must be standardized against the implementation.

## HTTP status codes

| Status | Meaning |
|---|---|
| 400 | Invalid/malformed request |
| 401 | Authentication required/failed |
| 403 | Authenticated but not permitted |
| 404 | Resource not found or intentionally not disclosed |
| 409 | Resource/state conflict |
| 422 | Semantically invalid input, if adopted |
| 429 | Rate limit exceeded |
| 500 | Unexpected server failure |
| 502/503/504 | Upstream/dependency/service failure where applicable |

## Validation errors

```json
{"error":{"code":"VALIDATION_ERROR","message":"The request contains invalid data.","fields":{"start_date":["Start date must be earlier than or equal to finish date."]}}}
```

## Authentication errors

```json
{"error":{"code":"AUTHENTICATION_REQUIRED","message":"Authentication is required."}}
```

Do not reveal whether a particular account exists when that would enable enumeration.

## Authorization errors

```json
{"error":{"code":"PERMISSION_DENIED","message":"You do not have permission to perform this action."}}
```

For sensitive resources, returning `404` instead of `403` can be appropriate where revealing resource existence is itself an information leak.

## Conflict errors

Use `409` for duplicate identifiers, invalid resource state, concurrent-update conflicts, or duplicate imports where appropriate.

## Rate limiting

Use `429 Too Many Requests` when a client exceeds a configured limit. Provide retry guidance where appropriate.

## Internal errors

Unexpected failures should return a generic message while diagnostic details remain server-side.

```json
{"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred.","request_id":"req-123"}}
```

## Client behavior

The frontend should distinguish validation, authentication expiry, authorization, not-found, conflict, network, and server failures. It should not blindly retry every failed request.

## Observability

Unexpected errors should be traceable through server-side logs using a request/correlation ID. Sensitive data must not be logged.

## Implementation note

The actual exception handler, serializer format, status-code conventions, and request-ID implementation must be verified against the repository.
