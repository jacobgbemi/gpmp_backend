# Security Testing

**Status:** Security testing baseline
**Last updated:** 2026-10-06

## Purpose

Define how security requirements are verified throughout the GlintPM Private development lifecycle.

## Testing layers

### 1. Static checks

- Dependency vulnerability scanning.
- Secret scanning.
- Static analysis/linting where security-relevant rules are available.
- Review of Django and frontend security configuration.

### 2. Automated application tests

Security-focused tests should cover:

- Authentication success and failure.
- Password reset behavior.
- Authorization by role.
- Organization isolation.
- Project/object-level access.
- Unauthorized state-changing requests.
- CSRF behavior where applicable.
- Input validation.
- File upload/import restrictions.
- Sensitive error handling.

### 3. API security testing

Test every protected endpoint for:

- Missing authentication.
- Insufficient permissions.
- Cross-organization object access.
- Cross-project object access.
- Identifier manipulation.
- Invalid payloads.
- Excessive request sizes.
- Pagination and filtering abuse.
- Replay/idempotency behavior where relevant.

### 4. Dynamic testing

Before important production releases, consider vulnerability scanning and penetration testing proportional to the application's risk and exposure.

## Security regression tests

Every discovered security vulnerability should result in:

1. A reproducible test where practical.
2. A code/configuration fix.
3. Regression verification.
4. Review of similar attack surfaces.
5. Documentation of the lesson learned.

## Release gate

High-severity unresolved security findings should block production release unless an explicit, documented risk acceptance exists.

## Test data

Do not use real production secrets or unnecessary personal/confidential information in development or test environments.

## Evidence

Keep useful evidence such as test results, dependency reports, remediation records, and security review notes in an appropriate controlled location.
