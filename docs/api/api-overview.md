# API Overview

- **Status:** Architectural/API documentation baseline
- **Date:** 2026-10-05

## Purpose

The GlintPM Private API is the controlled interface between the React frontend, Django backend, integrations, and future external clients. It handles authentication, authorization, validation, business operations, data retrieval, reporting, and controlled access to project-control data.

> **Implementation note:** The endpoint paths and payloads below are a proposed contract baseline. Repository routes, views, serializers, services, tests, and configuration remain the implementation source of truth.

## Base URL

Conceptually:

```text
/api/
```

If explicit versioning is adopted:

```text
/api/v1/
```

## Core principles

1. Authentication and authorization are enforced server-side.
2. Tenant boundaries are enforced server-side.
3. All untrusted input is validated.
4. Business rules do not live exclusively in the frontend.
5. Responses and errors are predictable and consistent.
6. Large collections are paginated.
7. Retry-sensitive operations are idempotent where appropriate.
8. Sensitive operations are auditable.

## Resource groups

```text
/api/
├── auth/
├── projects/
├── schedules/
├── costs/
├── progress/
├── risks/
├── reports/
└── errors/
```

## Request lifecycle

```text
HTTP Request → Authentication → Tenant Resolution → Authorization
→ Validation → Business Logic → Database/Integration → Audit → Response
```

## HTTP methods

| Method | Typical use |
|---|---|
| GET | Retrieve |
| POST | Create or execute an explicit action |
| PUT | Full replacement where appropriate |
| PATCH | Partial update |
| DELETE | Delete/archive where permitted |

## Pagination and filtering

Collection endpoints should support standardized pagination and controlled filtering/sorting as datasets grow.

Example:

```text
GET /api/projects/?status=active&page=2&page_size=25
```

## Idempotency

Imports, webhooks, asynchronous jobs, and other retry-prone operations should use an idempotency strategy where duplicate processing would be harmful.

## Security

Protected endpoints must apply authentication, authorization, tenant isolation, validation, secure transport, appropriate rate limiting, safe error responses, and audit logging for important actions.

## Endpoint documentation standard

Every production endpoint should document method, path, authentication, authorization, parameters, request body, validation, response schema, status codes, errors, pagination/filtering, and examples.
