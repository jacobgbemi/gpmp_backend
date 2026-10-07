# End-to-End Testing

**Status:** Testing baseline

## Purpose

End-to-end tests validate complete workflows across the frontend, API, authentication, database, and other required application services.

## Critical Workflows

At minimum, consider automated coverage for:

1. User authentication.
2. Organization/project access.
3. Project creation.
4. Schedule creation or import.
5. Schedule update/progress workflow.
6. Cost entry and review.
7. Risk creation and review.
8. Report generation/download.
9. Permission-restricted operations.
10. Logout/session expiration.

## Test Environment

E2E tests should use isolated test data and a dedicated test environment or equivalent controlled runtime. They must never depend on production records.

## Reliability

Avoid unnecessary timing-based assertions. Prefer explicit waits for application state, network completion, or visible UI conditions.

## Failure Scenarios

Critical workflows should include at least selected cases where:

- API calls fail.
- Sessions expire.
- Required data is missing.
- A permission check fails.
- A report cannot be generated.

## Implementation Note

The selected browser automation framework and executable E2E suite must be verified in the repository.
