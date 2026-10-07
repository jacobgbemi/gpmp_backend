# Rollback

## Purpose
Safely revert a problematic release.

## Triggers
Widespread failure, severe API errors, authentication failure, data-integrity risk, unacceptable performance, or critical security regression.

## Flow
`Detect → Confirm release correlation → Assess → Decide → Restore known-good release → Handle DB compatibility → Smoke test → Monitor`

Database migrations require special care. Review reversibility, backward compatibility, destructive changes, and data transformations before release.

Document failed release, symptoms, impact, rollback time, cause, and corrective action.
