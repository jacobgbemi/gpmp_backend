# Deployment

## Purpose
Define a controlled, repeatable process for deploying GlintPM Private.

## Principles
- Deploy reviewed and tested changes.
- Build from version-controlled source.
- Keep environment configuration outside source code.
- Run database migrations in a controlled step.
- Verify service health after deployment.
- Maintain a rollback path.

## Flow
`Review → Test → Build → Staging → Verify → Production → Monitor`

## Pre-deployment checklist
- Tests pass
- Security-sensitive changes reviewed
- Migrations reviewed
- Environment variables verified
- Backup/recovery position confirmed
- Rollback plan available

## Post-deployment
Verify authentication, critical APIs, database connectivity, background jobs, logs, metrics, and critical user workflows.

> Implementation note: actual CI/CD configuration and deployment manifests are the source of truth.
