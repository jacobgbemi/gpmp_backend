# Security Testing

**Status:** Testing baseline

## Purpose

Security testing verifies that security controls resist unauthorized access, data disclosure, privilege escalation, injection, and common application attacks.

## Authentication Tests

Test:

- Invalid credentials.
- Account/session expiration.
- Logout behavior.
- Password reset controls.
- Session fixation or reuse where applicable.
- Brute-force/rate-limiting protections where implemented.

## Authorization Tests

Test horizontal and vertical privilege escalation, including attempts to:

- Read another user's resources.
- Read another organization/project's resources.
- Modify unauthorized records.
- Perform administrator-only operations.
- Bypass frontend permission checks through direct API requests.

## Input Security

Test appropriate defenses against:

- SQL injection.
- Cross-site scripting.
- Command injection where relevant.
- Malformed JSON/input.
- Unsafe file uploads.
- Path traversal where file paths are accepted.

## Data Exposure

Verify that errors, APIs, logs, exports, and reports do not expose passwords, secrets, tokens, or unauthorized business data.

## Dependency Security

Dependencies should be monitored for known vulnerabilities and upgraded according to risk.

## Implementation Note

The actual scanners, security headers, dependency checks, authentication implementation, and CI security gates must be verified against the repository.
