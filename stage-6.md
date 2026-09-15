Perform Backend Stage 6 for GlintPM Private.

Do not introduce major new features.

Follow:

1. Business problem
2. Data model review
3. API review
4. Implementation review
5. Tests
6. Postman
7. Frontend integration review
8. Failure states
9. Database integrity
10. Security
11. Git
12. Documentation

========================================
1. BUSINESS PROBLEM
========================================

GlintPM Private will handle sensitive project information involving:

- project costs
- payment requests
- contractor information
- project documents
- project progress
- risks
- owner decisions

The platform must therefore be trustworthy before production deployment.

========================================
2. DATA MODEL REVIEW
========================================

Audit all models for:

- unnecessary fields
- missing constraints
- incorrect relationships
- missing indexes
- incorrect decimal fields
- orphan records
- cascade behavior
- duplicate data
- timestamp consistency

Review migrations for correctness.

========================================
3. API REVIEW
========================================

Audit:

- endpoint consistency
- pagination
- filtering
- validation
- error responses
- OpenAPI documentation
- HTTP status codes
- rate limiting
- N+1 queries
- API performance

========================================
4. IMPLEMENTATION REVIEW
========================================

Review the entire backend for:

- duplicated business logic
- weak abstractions
- unnecessary complexity
- missing transactions
- inefficient queries
- unsafe serializers
- poor exception handling
- secrets
- debug code
- production configuration problems

========================================
5. TESTING
========================================

Run:

pytest
Ruff
Django system checks
python manage.py check --deploy

Add missing:

- unit tests
- integration tests
- authorization tests
- IDOR tests
- file-security tests
- API tests
- database integrity tests

Aim for meaningful coverage, not arbitrary 100% coverage.

========================================
6. POSTMAN
========================================

Create a complete Postman regression collection covering:

Authentication
Organizations
Projects
Budget
Progress
Payments
Variations
Risks
Issues
Inspections
Evidence
Documents
Reports
Notifications
Decisions

Test both successful and unsuccessful workflows.

========================================
7. FRONTEND INTEGRATION
========================================

Verify the complete React → Django → PostgreSQL workflow.

Test:

- authentication
- token refresh
- navigation
- CRUD
- dashboard
- forms
- uploads
- reports
- errors
- permissions

========================================
8. FAILURE STATES
========================================

Systematically test:

400
401
403
404
409
422
429
500
503
network timeout
database unavailable
Redis unavailable
Celery failure
file upload failure
expired token

Ensure the frontend does not expose stack traces or sensitive backend information.

========================================
9. DATABASE INTEGRITY
========================================

Perform a full DBeaver/database audit.

Check:

- schema
- constraints
- indexes
- foreign keys
- orphan records
- duplicate records
- migrations
- transactions
- financial precision

Test backup and restore procedures.

========================================
10. SECURITY REVIEW
========================================

Perform a complete security audit covering:

Authentication
Authorization
IDOR
Tenant isolation
Passwords
JWT
CORS
CSRF
XSS
SQL injection
Mass assignment
File uploads
Sensitive data
Secrets
Logging
Error messages
Rate limiting
Security headers
Production DEBUG settings

Backend must remain the final authority for permissions.

========================================
11. GIT
========================================

Create a final hardening commit:

chore(backend): harden for production readiness

Ensure the repository contains no:

- secrets
- passwords
- private keys
- local database files
- sensitive uploads

========================================
12. DOCUMENTATION
========================================

Finalize:

README
Architecture documentation
Environment setup
Database setup
API documentation
Postman collection instructions
Deployment instructions
Backup/restore procedure
Security notes
Permission model
Important architecture decisions
Known limitations
Future improvements

Do not add new major product features during hardening.