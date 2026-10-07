# GlintPM Private — Authentication

## Purpose
Authentication establishes the identity of a user or system. It is distinct from authorization.

**Authentication:** Who are you?

**Authorization:** What are you allowed to do?

## Conceptual Flow

```text
User → Login → Credential / Identity Provider → Authentication Service
→ Session / Token → Protected API Requests
```

## Requirements
Authentication should:
- Protect application areas
- Protect credentials
- Handle expiration/revocation
- Support secure logout where applicable
- Avoid exposing secrets
- Produce appropriate security events

## Passwords
If local passwords are supported:
- Store only strong password hashes
- Never store plaintext passwords
- Never log passwords
- Use appropriate reset and rate-limiting controls

## Tokens / Sessions
Document:
- Token/session type
- Expiration
- Refresh behavior
- Revocation
- Storage
- Transport
- Rotation

For cookies, define Secure, HttpOnly, SameSite, and CSRF behavior.

## Organization Context
Identity establishes the user. Server-side authorization determines organization/project access. Client-provided organization IDs must never be trusted without verification.

## Failures
Handle invalid credentials, expired credentials, disabled users, rate limits, and malformed authentication data without leaking unnecessary information.

## Password Reset
Reset tokens should be unpredictable, expiring, and single-use where appropriate.

## MFA
MFA may be introduced where threat model or customer requirements justify it.

## Service Authentication
External integrations require securely stored, rotatable service credentials.

## Audit
Security-relevant events may include login, failed login, logout, password changes, resets, account disablement, and credential changes.

## Verification Status
The actual authentication library and session/token mechanism must be verified against the repository.
