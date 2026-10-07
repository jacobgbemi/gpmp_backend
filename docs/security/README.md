# GlintPM Private Security Documentation

This directory defines the security baseline for GlintPM Private.

## Documents

- `security-overview.md` — security objectives, principles, boundaries, and baseline threats.
- `authentication.md` — user identity and authentication requirements.
- `authorization.md` — server-side access-control model.
- `roles-and-permissions.md` — proposed roles and granular permissions.
- `threat-model.md` — assets, trust boundaries, threats, and abuse cases.
- `security-controls.md` — practical security-control checklist.
- `secrets-management.md` — handling and rotation of credentials and secrets.
- `data-protection.md` — classification, transport, storage, integrity, retention, and backups.
- `security-testing.md` — security verification and regression testing.
- `incident-response.md` — detection, containment, investigation, recovery, and lessons learned.

## Important implementation rule

These documents describe the intended security architecture and control baseline. They do not automatically prove that a control exists in the current codebase or production environment. Repository implementation, automated tests, infrastructure configuration, and operational evidence remain the source of truth.
