# Data Validation

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

Validation ensures information entering GlintPM Private is syntactically valid, semantically valid, authorized, and suitable for calculations and reporting.

## Validation layers

```text
Frontend Validation
        ↓
API / Serializer Validation
        ↓
Business Rule Validation
        ↓
Database Constraints
```

Frontend validation improves UX but is not a security boundary.

## API validation

Reject malformed requests, invalid identifiers, missing required fields, unsupported values, invalid dates, and oversized input.

## Business validation

Examples include:

- finish date cannot precede start date
- approved baselines cannot be edited as drafts
- users cannot submit progress for unauthorized projects
- unauthorized roles cannot approve changes
- references cannot cross tenant boundaries

## Cross-field validation

Rules such as `Actual Finish >= Actual Start` and approval timestamps matching approval status must be evaluated together.

## Referential validation

Referenced records must exist, belong to the correct tenant, be accessible to the requester, and be in a valid lifecycle state.

## Numeric and date validation

Define precision, range, unit, currency, rounding, timezone, reporting-period, and project-calendar rules where applicable.

## File validation

Imported files should be checked for format, size, encoding, required fields, duplicates, invalid values, malicious content, and tenant context.

## Error reporting

Use structured errors, for example:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data.",
    "fields": {
      "finish_date": ["Finish date cannot precede start date."]
    }
  }
}
```

## Testing

Test valid data, invalid data, boundaries, missing/conflicting values, unauthorized references, cross-tenant references, duplicate submissions, and import failures.
