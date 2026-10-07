# Projects API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Projects API manages project-level information and provides the parent resource for major project-control domains.

## Endpoints

```text
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{project_id}/
PATCH  /api/projects/{project_id}/
DELETE /api/projects/{project_id}/
```

Deletion may instead be implemented as archival.

## List projects

```http
GET /api/projects/?status=active&search=terminal&page=1&page_size=25
```

Conceptual response:

```json
{"results":[{"id":"project-id","code":"PRJ-001","name":"Example Project","status":"active","start_date":"2026-01-01","end_date":"2027-06-30"}]}
```

## Create project

```http
POST /api/projects/
```

```json
{"code":"PRJ-001","name":"Example Project","description":"Project description","start_date":"2026-01-01","end_date":"2027-06-30"}
```

## Update and archive

`PATCH /api/projects/{project_id}/` should permit only fields allowed by the lifecycle and user's permissions. Where historical records exist, archival is generally safer than destructive deletion.

## Authorization

The server should verify authentication, organization membership, project access, and action permission.

## Validation

At minimum validate project-code uniqueness rules, required name, logical dates, authorized organization, and valid lifecycle transitions.

## Related resources

Potential related routes include schedules, costs, progress, risks, and reports under the project resource.

## Common errors

`400` validation, `401` authentication, `403` permission, `404` unavailable project, `409` conflicting state.
