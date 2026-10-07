# Test Data

**Status:** Testing baseline

## Purpose

Define safe, representative, and repeatable data practices for automated and manual testing.

## Principles

Test data should be:

- Synthetic where possible.
- Isolated from production.
- Deterministic when tests require repeatability.
- Representative of real business cases.
- Safe to share within authorized development environments.

## Required Data Categories

Consider fixtures/factories for:

- Users.
- Organizations/tenants.
- Roles and permissions.
- Projects.
- Schedules.
- Activities and relationships.
- Baselines.
- Costs.
- Progress updates.
- Risks.
- Reports.
- Audit events.

## Boundary Data

Include cases such as:

- Empty datasets.
- Very large datasets.
- Maximum field lengths.
- Decimal monetary values.
- Zero values.
- Boundary dates.
- Missing optional values.
- Invalid values.
- Duplicate records.
- Cross-tenant identifiers.

## Sensitive Data

Do not use real passwords, API keys, access tokens, financial account credentials, or other production secrets in test fixtures.

Production data should not be copied into development/test environments unless an approved process exists for anonymization and access control.

## Data Reset

Automated tests should establish their own required state and clean up or isolate state so that test ordering does not determine results.

## Implementation Note

Actual fixtures, factories, seed scripts, anonymization processes, and test database lifecycle must be verified against the repository.
