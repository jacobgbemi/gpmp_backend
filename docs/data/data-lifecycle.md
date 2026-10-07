# Data Lifecycle

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## General lifecycle

```text
Create → Validate → Active/Working → Review/Approval → Historical/Archived → Retention → Controlled Deletion
```

Not every entity follows every stage.

## Project lifecycle

A project may conceptually progress through:

```text
Draft → Active → On Hold → Completed → Archived
```

## Schedule lifecycle

```text
Draft/Imported → Reviewed → Current → Superseded → Archived
```

Historical schedules should not be overwritten when needed for performance analysis.

## Baseline lifecycle

```text
Draft → Submitted → Approved → Superseded/Retired
```

Approved baselines should be protected from ordinary modification.

## Progress lifecycle

```text
Prepared → Submitted → Reviewed/Approved → Historical
```

## Risk lifecycle

```text
Identified → Assessed → Mitigating → Monitored → Closed
```

## Change lifecycle

```text
Proposed → Under Review → Approved/Rejected → Implemented → Closed
```

## Data correction

Historical data should not normally be silently overwritten. Corrections should preserve an appropriate audit trail describing what changed, why, who, and when.

## Archiving

Archiving should reduce operational clutter without destroying information required for contractual, reporting, or historical purposes.

## Deletion

Distinguish operational deletion, soft deletion, archival, and legally required deletion. Important project-control records should not be permanently deleted merely to hide historical changes.

## Retention

Retention should consider customer contracts, legal obligations, project duration, disputes, audit requirements, storage cost, and applicable privacy requirements.

## Implementation note

Actual lifecycle states and deletion behavior must be verified against implemented models and workflows.
