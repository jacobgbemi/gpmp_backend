# Progress API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Progress API records project and schedule performance observations and supports comparison against planned or baseline values.

## Conceptual endpoints

```text
GET  /api/projects/{project_id}/progress/
POST /api/projects/{project_id}/progress/
GET  /api/progress/{progress_id}/
PATCH /api/progress/{progress_id}/
GET  /api/projects/{project_id}/progress/summary/
```

## Progress record

```json
{"id":"progress-id","project_id":"project-id","data_date":"2026-10-01","reporting_period":"2026-09","planned_progress":"72.50","actual_progress":"68.20","comments":"Progress affected by delayed material delivery."}
```

The unit and scale of progress must be explicit.

## Data date

Official progress records should identify their data date so historical reporting remains reproducible.

## Lifecycle

A controlled workflow may be:

```text
Draft → Submitted → Reviewed/Approved → Historical
```

## Validation

Validate project access, data date, progress range, reporting period, duplicate official records, and restrictions on approved records.

## Schedule progress

Where activity-based progress is supported, fields may include actual start/finish, remaining duration, physical progress, and percent complete. The exact methodology must be defined by the scheduling domain.

## Derived metrics

Potential metrics include planned-vs-actual progress, progress variance, earned value measures, and forecast variance. Each needs a documented formula and authoritative inputs.

## Authorization and audit

Only authorized users may submit/update progress or approve status records. Important submissions, approvals, and corrections should be auditable.

## Common errors

`400` invalid data, `401` authentication, `403` insufficient permission, `404` unavailable, `409` conflicting reporting-period state.
