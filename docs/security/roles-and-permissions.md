# Roles and Permissions

**Status:** Security baseline
**Last updated:** 2026-10-06

## Purpose

Define a least-privilege role model for GlintPM Private without assuming that every role is already implemented.

## Suggested role model

| Role | Typical responsibility | Access principle |
|---|---|---|
| Organization Owner | Organization administration | Full organization administration |
| Organization Admin | Users, configuration, oversight | Administrative access within organization |
| Project Manager | Project delivery | Manage assigned projects |
| Planner / Scheduler | Planning and schedule management | Manage assigned schedules and planning data |
| Cost / Project Controls User | Cost and performance control | Manage assigned cost/control data |
| Reviewer / Approver | Formal review and approval | Review/approve assigned workflows |
| Viewer | Read-only stakeholder | Read-only authorized data |

These roles are a proposed baseline, not a claim that all roles currently exist in the implementation.

## Permission categories

Permissions should be granular enough to distinguish at least:

- View organization data.
- Manage organization users.
- View project.
- Create project.
- Update project.
- Archive project.
- View schedule.
- Modify schedule.
- Submit schedule.
- Approve schedule.
- View cost data.
- Modify cost data.
- Submit progress.
- Review progress.
- Manage risks.
- Generate reports.
- Export data.
- View audit events.

## Least privilege

Users should receive only the permissions necessary for their responsibilities. Elevated access should be intentional, reviewable, and removable.

## Separation of duties

Where practical, users who prepare a controlled submission should not be the only users capable of approving that submission. This is especially relevant to schedules, financial information, and formal project reporting.

## Permission changes

Changes to privileged roles or permissions should be authenticated, authorized, validated, and audited.

## Implementation note

The actual Django groups, permissions, policies, and role mappings must be documented from the repository once verified.
