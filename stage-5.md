Build Backend Stage 5 of GlintPM Private.

Follow the complete 12-step development workflow.

========================================
1. BUSINESS PROBLEM
========================================

The owner should not have to inspect dozens of project records.

GlintPM Private must convert project data into a concise executive view answering:

Where are we?

How much have we spent?

What is actually completed?

What could go wrong?

What payments are exposed?

What decisions require my attention?

The dashboard must be based on actual database data.

Do not introduce AI-generated conclusions at this stage.

========================================
2. DATA MODEL
========================================

Create:

Report
Notification
DecisionRequired
AuditLog

Reports:

MONTHLY_EXECUTIVE
PROJECT_HEALTH
PAYMENT_REVIEW
PROGRESS
RISK
SPECIAL

Decision statuses:

OPEN
RESOLVED
DEFERRED

Notifications should support:

- payment updates
- project status changes
- risk alerts
- variation updates
- new reports
- decision alerts

AuditLog should capture important actions.

Never store secrets in audit logs.

========================================
3. API
========================================

Finalize:

GET /api/projects/{id}/dashboard/

Create:

/api/projects/{id}/reports/
/api/reports/{id}/
/api/notifications/
/api/projects/{id}/decisions/
/api/audit/

========================================
4. IMPLEMENTATION
========================================

Dashboard should aggregate:

Financial Position
Schedule
Progress
Payments
Variations
Risks
Decisions
Contractor performance

Use deterministic business rules.

Integrate Celery + Redis for:

- report generation
- notifications
- background processing

Do not move ordinary CRUD operations into asynchronous jobs unnecessarily.

========================================
5. TESTS
========================================

Test:

- dashboard calculations
- report generation
- notifications
- decision lifecycle
- audit logging
- permissions
- background jobs
- failure/retry behavior

Test that dashboard values change correctly when underlying data changes.

========================================
6. POSTMAN
========================================

Test:

Project dashboard
→ create decision
→ resolve decision
→ generate report
→ retrieve report
→ generate notification
→ retrieve notifications

Verify audit records.

========================================
7. FRONTEND
========================================

Build the executive experience:

Dashboard

Reports

Notifications

Decision Center

The dashboard should prioritize:

1. Project Health
2. Financial Position
3. Schedule
4. Progress
5. Payment Exposure
6. Variations
7. Risks
8. Decisions Required

The owner should understand project condition within approximately 30 seconds.

========================================
8. FAILURE STATES
========================================

Test:

- failed report generation
- unavailable Redis
- Celery failure
- missing project
- unauthorized report
- invalid decision transition
- notification failure
- partial dashboard data

The UI should gracefully communicate degraded states.

========================================
9. DATABASE INTEGRITY
========================================

Use DBeaver to inspect:

- reports
- notifications
- decisions
- audit logs

Verify:

- relationships
- timestamps
- foreign keys
- audit completeness
- no orphan records
- no duplicated notifications caused by retries

========================================
10. SECURITY
========================================

Review:

- report authorization
- notification privacy
- audit log access
- organization isolation
- sensitive information
- background task permissions
- API authorization

Audit logs must not become an unintended data-leak mechanism.

========================================
11. GIT
========================================

Commit:

feat(backend): add executive reporting notifications and audit

========================================
12. DOCUMENTATION
========================================

Document:

- dashboard KPI calculations
- report types
- notification triggers
- decision workflow
- audit strategy
- Celery architecture
- retry/idempotency decisions

========================================
13. ADD TO UNFOLD ADMIN
========================================
Report
Notification
DecisionRequired
AuditLog