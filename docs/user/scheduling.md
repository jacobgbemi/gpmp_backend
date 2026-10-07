# Scheduling

**Status:** User guide baseline  
**Last updated:** 2026-10-06

## Purpose

Explain the core project scheduling workflow.

## Schedule Lifecycle

A schedule may progress through:

```text
Draft
  ↓
Reviewed
  ↓
Approved/Baselined
  ↓
Updated
  ↓
Superseded
```

The actual lifecycle depends on project governance and implementation.

## Creating a Schedule

Typical information includes:

- schedule name/version;
- project;
- planned start;
- planned finish;
- data date;
- calendar;
- activities;
- relationships;
- constraints;
- milestones.

## Activities

Activities should have clear:

- identifiers;
- descriptions;
- durations;
- dates;
- relationships;
- status;
- progress information.

Avoid duplicate activity IDs within the same schedule context.

## Relationships

Common relationships include:

- Finish-to-Start;
- Start-to-Start;
- Finish-to-Finish;
- Start-to-Finish.

Use relationships that represent actual project logic rather than forcing dates manually.

## Baselines

A baseline represents an approved reference plan against which current performance can be compared.

Record:

- baseline version;
- approval date;
- owner;
- applicable schedule;
- change history.

## Schedule Updates

During each reporting period:

1. Confirm the data date.
2. Record actual starts/completions.
3. Update remaining durations or forecast dates.
4. Record progress.
5. Recalculate the schedule.
6. Review critical activities.
7. Compare against baseline.
8. Issue the reporting output.

## Schedule Quality

Review for:

- open-ended activities;
- excessive constraints;
- missing logic;
- unrealistic durations;
- invalid dates;
- duplicate IDs;
- broken calendars;
- unexplained baseline variance.
