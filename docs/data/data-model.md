# Data Model

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

This document defines the conceptual data model for GlintPM Private. It establishes major entities, ownership relationships, and domain boundaries without claiming every entity is already implemented.

Repository models, migrations, serializers, and tests remain the source of truth for the implemented schema.

## Core domain model

```text
Organization
├── Users / Memberships
├── Projects
│   ├── Schedules
│   │   ├── Activities
│   │   ├── Relationships
│   │   ├── Calendars
│   │   └── Baselines
│   ├── Progress Updates
│   ├── Costs
│   ├── Risks
│   ├── Issues
│   ├── Changes
│   ├── Actions
│   ├── Decisions
│   └── Reports
└── Audit Events
```

## Primary entities

### Organization

Represents a customer/company/tenant using the platform.

Typical attributes: identifier, name, status, configuration, timestamps.

### User

Represents an authenticated person. Typical attributes include identity information, account status, authentication metadata, and timestamps.

### Membership

Connects a user to an organization and establishes organization-level role/access.

### Project

Represents a project controlled through GlintPM. Typical attributes include project code, name, description, client/owner, project type, dates, status, organization, and timestamps.

### Schedule

Represents a project schedule or scheduling dataset, including project, name, status, data date, calendar, source, and version.

### Activity

Represents a schedule activity/work item, including code, name, type, dates, duration, progress, and responsibility.

### Baseline

Represents an approved/reference plan against which actual performance can be compared.

### Progress Update

Represents a recorded project status/progress observation.

### Cost Record

Represents budget, commitment, actual, forecast, or other project financial information.

### Risk

Represents a project risk and its assessment/response.

### Issue

Represents a problem requiring monitoring or resolution.

### Change

Represents a proposed or approved project change.

### Action

Represents an action assigned to a person or team.

### Decision

Represents an important management/project decision.

### Report

Represents generated or persisted reporting output/metadata.

### Audit Event

Represents a historical record of a significant system or business event.

## Ownership

Preferred ownership chain:

```text
Organization → Project → Project Domain Records
```

Records that are organization-wide may attach directly to Organization.

## Relationships

Use explicit foreign-key relationships rather than duplicated names. Project belongs to Organization; Schedule belongs to Project; Activity belongs to Schedule; and project-control records belong to the relevant Project.

## Historical data

Business-critical historical states should not be silently overwritten. Use versioning, snapshots, effective dates, or dedicated history records where appropriate.

## Design principles

1. Model business concepts explicitly.
2. Preserve tenant ownership.
3. Enforce relationships with database constraints.
4. Avoid unnecessary duplication.
5. Keep authoritative data separate from derived reporting data.
6. Preserve important historical states.
7. Use transactions for multi-entity operations.
