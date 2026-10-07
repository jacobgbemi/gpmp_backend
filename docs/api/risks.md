# Risks API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Risks API manages project risks, assessments, ownership, responses, and lifecycle status.

## Conceptual endpoints

```text
GET  /api/projects/{project_id}/risks/
POST /api/projects/{project_id}/risks/
GET  /api/risks/{risk_id}/
PATCH /api/risks/{risk_id}/
DELETE /api/risks/{risk_id}/
POST /api/risks/{risk_id}/close/
```

## Risk record

```json
{"id":"risk-id","project_id":"project-id","title":"Material delivery delay","description":"Potential delay to critical materials.","probability":4,"impact":5,"score":20,"status":"open","response":"Identify alternate supplier."}
```

## Risk scoring

If probability and impact scoring is used, the formula must be explicit. For example:

```text
Risk Score = Probability × Impact
```

This is illustrative until formally adopted.

## Lifecycle

```text
Identified → Assessed → Mitigating → Monitored → Closed
```

## Validation

Validate project ownership, scoring ranges, authorized owners, required closure information, and consistent score calculation.

## Authorization

Permissions may distinguish viewing, creating, editing, assigning, changing status, and closing risks.

## Reporting

Potential summaries include open/high risks, exposure, risks by category, and risks by owner. Values must derive from authoritative records.

## Audit

Score, owner, response, status, and closure changes should be auditable.

## Common errors

`400` invalid data, `401` authentication, `403` permission, `404` unavailable resource, `409` invalid lifecycle transition.
