# ADR-003: Authentication Strategy

- **Status:** Accepted — architectural baseline
- **Date:** 2026-10-04

## Context

GlintPM Private may contain commercially sensitive organizational and project information. Users must be reliably identified before accessing protected resources.

Authentication must support future organization membership, roles, permissions, audit records, and potentially enterprise identity providers.

## Decision

Use a **server-controlled authentication model based on Django's authentication capabilities and the application's API authentication layer**.

The exact session, token, or hybrid mechanism must be selected according to the deployed frontend/API architecture and documented in implementation configuration.

Authentication and authorization remain separate concerns.

```text
Authentication → Who are you?
Authorization  → What are you allowed to do?
```

## Core requirements

If local passwords are supported:

- never store plaintext passwords
- use Django-supported secure password hashing
- never log credentials
- use secure, expiring password-reset tokens
- protect authentication endpoints from abuse

The chosen session/token mechanism must address expiration, logout/revocation, secure transport, secure storage, CSRF where applicable, and token leakage.

A successful login must not automatically grant access to every organization or project.

## Authentication flow

```text
User → Login → Django Authentication → Session/Token
     → Protected API Request → Authentication Verification
     → Authorization Check → Resource Access
```

## Password reset

Password reset should avoid account enumeration, use cryptographically secure expiring tokens, limit token reuse, and record relevant security events.

## Future identity providers

Enterprise SSO or other identity providers may be introduced later through a clear identity boundary so external authentication cannot bypass GlintPM authorization.

## MFA

MFA may be introduced if product risk or customer requirements justify it. MFA does not replace authorization or tenant isolation.

## Alternatives considered

### Custom authentication system

Rejected because implementing credential storage, session management, reset flows, and security controls independently creates unnecessary risk.

### Frontend-only authentication

Rejected because the frontend cannot be the authoritative security boundary.

### External identity provider only

Not selected as the initial baseline because organizations may need local accounts.

## Consequences

### Positive

- Mature Django security foundation.
- Server-controlled identity.
- Strong basis for organization membership and authorization.
- Future SSO/MFA compatibility.

### Negative

- Authentication configuration must be carefully secured.
- Frontend/API integration requires explicit session/token handling.
- Security testing and monitoring are required.

## Implementation notes

The exact authentication package, token/session mechanism, endpoints, cookie configuration, and middleware must be verified against the repository.
