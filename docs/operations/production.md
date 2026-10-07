# Production Operations

## Purpose
Define standards for safely operating GlintPM Private in production.

## Standards
Production should prioritize availability, security, data integrity, observability, controlled change, and recoverability.

Disable debug behavior, enforce HTTPS, restrict hosts/origins, protect authentication, restrict database access, and expose only required services.

Production access should be limited to authorized personnel. Avoid direct database edits; prefer controlled application migrations and workflows.

## Operational checks
Review uptime, errors, API latency, database health, resources, backups, authentication failures, and security alerts.
