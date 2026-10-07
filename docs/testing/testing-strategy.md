# Testing Strategy

**Status:** Testing baseline  
**Applies to:** GlintPM Private

## Purpose

Define a layered testing strategy that provides confidence in business logic, APIs, database behavior, frontend behavior, security controls, and critical end-to-end workflows.

## Testing Pyramid

```text
                 End-to-End
              /             \
          Integration      UI/System
         /                         \
       API          Component/Frontend
         \                         /
             Unit Tests
```

The project should favor fast, deterministic unit tests while maintaining sufficient integration and end-to-end coverage for high-risk workflows.

## Test Layers

| Layer | Primary purpose |
|---|---|
| Unit | Validate isolated functions, services, validators, and business rules |
| Integration | Validate interaction between application components and infrastructure |
| API | Validate HTTP contracts, validation, authentication, authorization, and errors |
| Frontend | Validate components, state, forms, navigation, and user interactions |
| End-to-end | Validate complete critical workflows from the user's perspective |
| Security | Validate security controls and common abuse cases |
| Failure | Validate graceful behavior under dependency and data failures |

## Quality Gates

A change should not be considered production-ready when it introduces failing tests, breaks a documented API contract, creates an unacceptable security regression, or leaves critical business logic untested.

## Priority

Testing priority should be highest for:

1. Authentication and authorization.
2. Tenant/organization isolation.
3. Financial and cost calculations.
4. Schedule and progress calculations.
5. Data integrity and destructive operations.
6. Audit logging.
7. Report generation.
8. Core project workflows.

## Test Properties

Tests should be:

- Deterministic.
- Isolated where practical.
- Repeatable.
- Readable.
- Fast at lower layers.
- Independent of production data.
- Safe to run in CI.

## Implementation Note

The exact test framework, directory structure, CI gates, coverage thresholds, and test commands must be verified against the repository before being treated as implemented standards.
