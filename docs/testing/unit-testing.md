# Unit Testing

**Status:** Testing baseline

## Purpose

Unit tests validate small pieces of application logic independently from external systems whenever practical.

## Recommended Targets

Backend unit tests should cover:

- Domain/business rules.
- Validation functions.
- Calculation functions.
- Schedule calculations.
- Cost calculations.
- Progress calculations.
- Risk scoring logic.
- Permission predicates.
- Serialization/deserialization logic where isolated.
- Utility functions.

Frontend unit/component tests should cover:

- Pure utility functions.
- Form validation.
- Data transformation.
- State transitions.
- Reusable components.

## Principles

A unit test should generally have one clear reason to fail and should avoid requiring a real database, network, filesystem, or external service unless the dependency itself is the subject of an integration test.

## Example Structure

```text
Arrange
  ↓
Act
  ↓
Assert
```

## Business Rules

High-value calculations should include normal, boundary, invalid, and exceptional cases.

For example, a cost calculation should test:

- Zero values.
- Positive values.
- Decimal precision.
- Missing values where invalid.
- Negative values where prohibited.
- Currency consistency.
- Rounding behavior.

## Mocking

Mock external dependencies only when doing so improves isolation. Avoid excessive mocking of internal implementation details because it can make tests pass while real behavior is broken.

## Implementation Note

The actual unit-testing framework and test locations must be confirmed from the repository.
