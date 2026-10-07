# Backups

## Purpose
Protect GlintPM Private data against loss and corruption.

## Scope
Consider production database, required uploaded files, critical configuration, and deployment metadata.

## Principles
Backups should be automated, protected, separate from the primary workload, retained appropriately, monitored, and tested through restoration.

Use encryption at rest/in transit where appropriate. A successful backup job is not proof of recoverability: periodically restore and verify data, schema compatibility, and critical records.

Backup failures must alert operators and be investigated.
