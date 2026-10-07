# Data Dictionary

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

This document defines the expected meaning of major GlintPM Private data elements. Exact field names, types, nullability, constraints, and indexes must be verified against the repository.

## Core entities

| Entity | Key data concepts |
|---|---|
| Organization | ID, name, status, configuration, created/updated timestamps |
| User | ID, identity, email, account status, timestamps |
| Membership | user, organization, role, status, created timestamp |
| Project | ID, code, name, description, organization, dates, status |
| Schedule | ID, project, name, data date, status, source, version |
| Activity | ID, activity code, name, schedule, dates, duration, progress, status |
| Baseline | ID, scope, name, status, approver, approval timestamp |
| Progress Update | ID, project, reporting period, data date, progress, comments, recorder |
| Cost Record | ID, project, cost type, amount, currency, period, source, status |
| Risk | ID, project, description, probability, impact, score, response, owner, status |
| Issue | ID, project, description, priority, owner, due date, status |
| Change Request | ID, project, description, impact, status, requester, approver |
| Action | ID, project, owner, due date, description, status |
| Decision | ID, project, decision, owner/approver, date, status |
| Report | ID, project/scope, reporting period, type, generated metadata |
| Audit Event | ID, organization, actor, event type, resource, timestamp, change summary |

## Data conventions

- IDs should be stable and unique.
- Monetary values should use exact numeric representations where precision matters.
- Currency should be explicit.
- Timestamps should follow a consistent timezone strategy.
- Status values should be controlled.
- Human-readable codes should not replace stable primary identifiers.
- External identifiers should be distinct from internal identifiers.
