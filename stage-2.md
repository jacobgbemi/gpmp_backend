Build Backend Stage 2 of GlintPM Private.

Follow the complete workflow:

1. Business problem
2. Data model
3. API design
4. Backend implementation
5. Automated tests
6. Postman testing
7. Frontend integration
8. Failure-state testing
9. Database integrity
10. Security/permissions
11. Git commit
12. Documentation

Do not implement Variations, Risks, Issues, Inspections, Documents, Reports or Notifications yet.

========================================
1. BUSINESS PROBLEM
========================================

The core problem GlintPM Private solves is:

A high-value property owner should be able to understand:

- how much the project should cost
- how much has been spent
- how much has been committed
- how much the project is forecast to cost
- how much work is actually completed
- whether the project is ahead or behind schedule
- what contractor payment requests are being made
- what amount GlintPM recommends
- what has been approved
- what has actually been paid

The system must establish the financial and progress truth of a project.

========================================
2. DATA MODEL
========================================

Create:

Project
ProjectBudget
BudgetItem
ProgressUpdate
PaymentApplication

Project:

- UUID
- organization
- name
- project_code
- description
- location
- client_name
- contractor_name
- project_type
- contract_value
- planned_start_date
- planned_end_date
- actual_start_date
- actual_end_date
- status
- currency
- timestamps

Statuses:

PLANNING
ACTIVE
ON_HOLD
COMPLETED
CANCELLED

Budget:

ProjectBudget

BudgetItem should support:

- category/code
- description
- original_amount
- approved_amount
- actual_amount
- committed_amount

Use DecimalField for all money.

ProgressUpdate must preserve historical updates.

Store:

- reporting date
- planned progress
- actual progress
- notes
- submitted by

PaymentApplication must distinguish:

- amount_requested
- amount_recommended
- amount_approved
- amount_paid

Statuses:

DRAFT
SUBMITTED
UNDER_REVIEW
RECOMMENDED
APPROVED
PARTIALLY_PAID
PAID
REJECTED

Never collapse these amounts into one field.

========================================
3. API DESIGN
========================================

Create:

GET /api/projects/
POST /api/projects/
GET /api/projects/{id}/
PATCH /api/projects/{id}/
DELETE /api/projects/{id}/

Budget:

GET /api/projects/{id}/budget/
POST /api/projects/{id}/budget/

Progress:

GET /api/projects/{id}/progress/
POST /api/projects/{id}/progress/

Payments:

GET /api/projects/{id}/payments/
POST /api/projects/{id}/payments/
GET /api/payments/{id}/
POST /api/payments/{id}/review/

Dashboard:

GET /api/projects/{id}/dashboard/

Dashboard should return:

- original budget
- approved budget
- actual spend
- committed cost
- forecast final cost
- cost variance
- planned progress
- actual progress
- schedule variance
- pending payments

========================================
4. IMPLEMENTATION
========================================

Implement models, serializers, views, services, selectors and permissions.

Payment review logic must be implemented in a service layer.

For example:

PaymentService.review()

The service should validate the payment request and calculate/store the recommendation.

Use transactions where multiple records must remain consistent.

Every project must belong to an organization.

========================================
5. TESTS
========================================

Test:

- project CRUD
- organization isolation
- budget calculations
- progress history
- payment creation
- payment review
- requested/recommended/approved/paid distinction
- invalid payment transitions
- dashboard calculations
- money precision
- date validation
- project status validation

Test realistic financial scenarios.

========================================
6. POSTMAN
========================================

Create a complete Postman workflow:

Login
→ Create organization
→ Create project
→ Create budget
→ Add progress update
→ Create payment
→ Review payment
→ Retrieve dashboard

Verify every response.

Create environment variables:

base_url
access_token
organization_id
project_id
payment_id

Test:

- valid requests
- unauthorized requests
- invalid IDs
- invalid payloads
- wrong organization

========================================
7. FRONTEND
========================================

Build only the frontend needed for this stage:

- Projects list
- Project creation
- Project detail
- Owner dashboard
- Progress page
- Payments page
- Payment detail/review

Dashboard should prioritize:

Budget
Forecast Final Cost
Physical Progress
Schedule Variance
Pending Payments
Project Health

Use backend values.

Do not hard-code the ₦500m demo values into React.

========================================
8. FAILURE STATES
========================================

Test and implement UI/API handling for:

400
401
403
404
409
422
429
500
network failure

Also test:

- invalid payment
- missing project
- unauthorized project
- negative money values
- impossible progress values
- invalid status transitions
- duplicate project codes

========================================
9. DATABASE INTEGRITY
========================================

Use DBeaver to inspect:

projects
project_budgets
budget_items
progress_updates
payment_applications

Check:

- foreign keys
- decimal precision
- indexes
- unique constraints
- historical progress records
- payment amounts
- organization relationships

Verify no payment can exist without a valid project.

========================================
10. SECURITY
========================================

Review:

- project-level permissions
- organization isolation
- payment authorization
- role restrictions
- object-level access
- mass assignment
- serializer fields
- IDOR

A user must never access another organization's project by changing the UUID.

========================================
11. GIT
========================================

Commit:

feat(backend): add projects cost progress and payments

========================================
12. DOCUMENTATION
========================================

Document:

- financial data model
- payment lifecycle
- dashboard calculation rules
- progress calculation approach
- permission rules
- why requested/recommended/approved/paid are separate
- API examples

Do not proceed until Postman, frontend integration, tests, DB checks and security checks pass.