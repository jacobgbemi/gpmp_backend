# Reports API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Reports API provides controlled access to project-control reports, dashboards, summaries, and report-generation operations. Reports should remain traceable to authoritative data.

## Conceptual endpoints

```text
GET  /api/projects/{project_id}/reports/
POST /api/projects/{project_id}/reports/
GET  /api/reports/{report_id}/
POST /api/reports/{report_id}/generate/
GET  /api/reports/{report_id}/download/
```

## Report types

Potential types include project status, schedule performance, cost performance, progress, risk, change, executive summary, dashboard, and variance reports.

## Report request

```json
{"report_type":"project_status","project_id":"project-id","data_date":"2026-10-01","baseline_id":"baseline-id"}
```

## Report metadata

Where relevant, identify project, organization, report type, reporting period, data date, baseline reference, generation time, requesting user, and calculation/report version.

## Asynchronous generation

Large reports should use a background workflow:

```text
Request → Create Job → Process → Store Result → Expose Status → Download
```

## Authorization

Reports must respect organization and project boundaries. Financial and executive reports may require additional permissions.

## Export formats

Potential formats include JSON, CSV, XLSX, and PDF. Actual support is implementation-dependent.

## Performance

Avoid repeating expensive calculations on every dashboard request. Potential strategies include indexes, aggregates, materialized views, scheduled jobs, and reporting tables.

## Freshness

Reports should identify data date and generation time when material to interpretation.

## Audit

Sensitive report generation/download operations may be recorded in the audit trail.

## Common errors

`400` invalid request, `401` authentication, `403` denied, `404` unavailable, `409` generation conflict, `202` accepted for asynchronous processing where appropriate.
