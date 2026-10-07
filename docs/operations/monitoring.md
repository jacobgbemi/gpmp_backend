# Monitoring

## Purpose
Define signals needed to detect service degradation.

## Monitor
- Infrastructure: CPU, memory, disk, network, process/container health.
- Application: request rate, latency, errors, auth failures, jobs, database errors.
- API: 5xx rate, abnormal 4xx rate, latency, timeouts.
- Database: connections, slow queries, failures, locks, storage, replication where applicable.
- Business workflows: authentication, project creation, schedules, progress, reporting, imports.

Alerts should be actionable and include severity, owner, threshold, escalation path, and runbook.

Health checks should expose only non-sensitive information.
