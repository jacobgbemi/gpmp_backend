# Authentication API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

Authentication establishes the identity of API clients. It does not determine what a user may access; authorization and tenant isolation are separate server-side controls.

> The exact authentication mechanism and routes must be verified against the repository.

## Conceptual endpoints

```text
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/password-reset/
POST /api/auth/password-reset/confirm/
GET  /api/auth/me/
```

## Login

```http
POST /api/auth/login/
Content-Type: application/json
```

```json
{"email":"user@example.com","password":"********"}
```

A successful response must never expose passwords, password hashes, or secrets. The exact session/token response depends on the implemented authentication mechanism.

## Logout

```http
POST /api/auth/logout/
```

Logout should invalidate the relevant session/token according to the implementation.

## Current user

```http
GET /api/auth/me/
```

Conceptual response:

```json
{"id":"user-id","name":"Example User","email":"user@example.com"}
```

## Password reset

Password reset should avoid account enumeration, use secure expiring tokens, limit token reuse, and record relevant security events.

## Authentication failures

Typical response: `401 Unauthorized`. Error messages should not reveal whether a particular account exists.

## Security requirements

- Never log passwords or secrets.
- Use secure password hashing.
- Protect authentication endpoints from abuse.
- Require HTTPS in production.
- Use appropriate secure cookie flags when cookies are used.
- Handle CSRF where applicable.
- Audit important authentication/security events.

## Organization context

Successful authentication does not grant access to every organization. Subsequent authorization must establish valid organization membership and project access.

## Implementation note

The exact package, session/token format, refresh behavior, CSRF handling, routes, and middleware must be verified against the implementation.
