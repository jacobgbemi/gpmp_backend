# Schedules API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Schedules API manages schedules, activities, relationships, baselines, and schedule status information where supported.

## Conceptual resources

```text
Project → Schedule → Activities / Relationships / Calendar / Baselines
```

## Endpoints

```text
GET  /api/projects/{project_id}/schedules/
POST /api/projects/{project_id}/schedules/
GET  /api/schedules/{schedule_id}/
PATCH /api/schedules/{schedule_id}/
GET  /api/schedules/{schedule_id}/activities/
POST /api/schedules/{schedule_id}/activities/
GET  /api/schedules/{schedule_id}/baselines/
POST /api/schedules/{schedule_id}/baselines/
```

## Schedule

Conceptual fields include schedule ID, project ID, name, data date, status, source, and version.

## Activities

Potential fields include activity code, name, type, planned/forecast/actual dates, duration, progress, float, responsible party, and status.

## Relationships

Typical scheduling relationships include Finish-to-Start, Start-to-Start, Finish-to-Finish, and Start-to-Finish. Validation should prevent invalid self-references and unauthorized cross-schedule references.

## Baselines

Baselines are controlled reference states. A conceptual workflow is:

```text
Draft → Submitted → Approved → Superseded
```

Approved baselines should not be silently overwritten.

## Imports

Supported schedule imports should follow parse → validate → map → preview → commit → audit. See `docs/data/data-import-export.md`.

## Authorization and validation

Verify authentication, organization membership, project access, and action permission. Validate dates, activity uniqueness, schedule ownership, relationship references, and baseline state.

## Performance

Large schedules may contain thousands of activities, so pagination, filtering, bulk operations, and asynchronous processing may be required.

## Common errors

`400` invalid data, `401` unauthenticated, `403` unauthorized, `404` unavailable, `409` conflicting schedule state.
