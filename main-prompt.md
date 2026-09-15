You are a senior Django/Python software architect building the backend for a scalable SaaS product called:

GLINTPM PRIVATE
Owner's Project Control & Assurance Platform

PRODUCT POSITIONING

GlintPM Private provides independent project controls, monitoring, assurance and executive intelligence for owners of high-value construction/property projects.

The platform is NOT intended to replace architects, engineers, quantity surveyors, lawyers or contractors.

Its primary purpose is to give the property owner an independent, structured view of:

1. Cost
2. Schedule
3. Physical progress
4. Contractor performance
5. Payments
6. Variations
7. Risks/issues
8. Site evidence
9. Documents
10. Decisions
11. Executive project status

The MVP must be designed so it can later evolve into a full multi-tenant SaaS platform.

TECHNOLOGY

Use:

- Python 3.12+
- Django 5+
- Django REST Framework
- PostgreSQL
- JWT authentication
- django-filter
- Celery + Redis for background jobs where appropriate
- Object/file storage abstraction compatible with S3/Azure Blob
- OpenAPI/Swagger documentation
- pytest
- Docker/Docker Compose
- environment variables for all secrets/configuration

ARCHITECTURE

Use a modular Django architecture.

Recommended apps:

accounts/
organizations/
projects/
documents/
progress/
costs/
payments/
variations/
risks/
inspections/
contractors/
reports/
notifications/
audit/

Do not create one huge models.py.

The system must use UUIDs as public identifiers.

MULTI-TENANCY

The application must support:

Organization
    └── Users
    └── Projects
    └── Documents
    └── Reports
    └── Contractors
    └── etc.

Every project belongs to an organization.

Every organization can have multiple users and multiple projects.

A user must NEVER be able to access another organization's data.

Implement organization-level data isolation at the API/service layer.

USER ROLES

Create role-based permissions:

- Platform Admin
- Organization Admin
- Project Manager
- Project Controls
- Site Inspector
- Consultant
- Client/Owner
- Viewer

The Owner role should have read access to executive information but should not automatically gain administrative access.

CORE MODELS

Organization

Fields:
- id
- name
- legal_name
- email
- phone
- country
- timezone
- currency
- logo
- created_at
- updated_at

User

Extend Django AbstractUser.

Fields:
- id
- email
- first_name
- last_name
- phone
- is_active
- created_at
- updated_at

OrganizationMembership

Fields:
- id
- organization
- user
- role
- status
- created_at

Project

Fields:

- id
- organization
- name
- project_code
- description
- project_type
- location
- client_name
- contractor_name
- original_budget
- approved_budget
- current_forecast_cost
- currency
- start_date
- planned_completion_date
- forecast_completion_date
- actual_completion_date
- status
- created_at
- updated_at

Project types should support:

- Residential
- Commercial
- Industrial
- Hospitality
- Estate Development
- Infrastructure
- Renovation
- Other

Project status:

- Planning
- Active
- On Hold
- Completed
- Closed

PROJECT BASELINE

Create models for:

ProjectBudget
BudgetItem
ScheduleBaseline
Milestone
ActivitySummary

Do not attempt to recreate Primavera P6 in the MVP.

The platform should store summary schedule information rather than becoming a scheduling engine.

BUDGET

BudgetItem:

- project
- category
- description
- original_amount
- approved_amount
- committed_amount
- actual_amount
- forecast_amount
- variance
- status

Support categories such as:

- Civil
- Structural
- Architectural
- MEP
- Finishes
- External Works
- Professional Fees
- Procurement
- Other

PROGRESS

Create:

ProgressUpdate

Fields:
- project
- reporting_period
- planned_progress_percent
- actual_progress_percent
- progress_variance
- narrative
- submitted_by
- approved_by
- created_at

Milestone:

- project
- name
- planned_date
- forecast_date
- actual_date
- status

PAYMENTS

Create PaymentApplication:

- project
- contractor
- application_number
- amount_requested
- amount_recommended
- amount_approved
- amount_paid
- submission_date
- review_date
- payment_date
- status
- reviewer_notes

Statuses:

- Submitted
- Under Review
- Query Raised
- Recommended
- Approved
- Paid
- Rejected

The system must distinguish:

AMOUNT REQUESTED

from

AMOUNT RECOMMENDED

from

AMOUNT APPROVED

from

AMOUNT PAID.

This is a core feature.

VARIATIONS

Create Variation:

- project
- variation_number
- title
- description
- requested_amount
- assessed_amount
- approved_amount
- status
- reason
- requested_date
- approved_date
- notes

Statuses:

- Proposed
- Under Review
- Recommended
- Approved
- Rejected
- Implemented

RISKS AND ISSUES

Create Risk:

- project
- title
- description
- category
- probability
- impact
- risk_score
- mitigation
- owner
- due_date
- status
- created_at
- updated_at

Support:

- Cost
- Schedule
- Quality
- Procurement
- Contractor
- Design
- Commercial
- Regulatory
- Safety
- Other

Create Issue separately from Risk.

INSPECTIONS

Create:

Inspection

Fields:
- project
- inspection_date
- inspector
- location
- summary
- overall_status
- recommendations

InspectionItem:

- inspection
- category
- description
- status
- severity
- recommendation

Categories:

- Progress
- Quality
- Materials
- Contractor
- Safety
- Commercial
- Documentation
- Other

SITE EVIDENCE

Create ProjectEvidence:

- project
- inspection
- title
- description
- evidence_type
- file
- captured_at
- uploaded_by
- latitude (optional)
- longitude (optional)
- metadata

Evidence types:

- Photo
- Video
- Document
- Drawing
- Certificate
- Invoice
- Other

Do not expose sensitive file URLs publicly.

DOCUMENT MANAGEMENT

Create:

DocumentFolder
Document

Documents should support:

- project documents
- contracts
- BOQs
- drawings
- schedules
- payment documents
- reports
- correspondence
- inspection evidence

Track:

- uploaded_by
- uploaded_at
- document_type
- version
- status

AUDIT TRAIL

Every important change must be logged.

Create AuditLog:

- organization
- user
- action
- model_name
- object_id
- old_values
- new_values
- timestamp
- IP address where appropriate

Important actions include:

- payment changes
- variation changes
- risk changes
- project changes
- user/permission changes
- document uploads/deletions
- report publication

EXECUTIVE DASHBOARD API

Create a dedicated dashboard API.

Endpoint concept:

GET /api/projects/{project_id}/dashboard/

Return:

project information

financial KPIs:
- original budget
- approved budget
- actual spend
- committed cost
- forecast final cost
- cost variance
- approved variations

schedule KPIs:
- planned progress
- actual progress
- progress variance
- planned completion
- forecast completion
- schedule variance

risk KPIs:
- total risks
- high risks
- critical risks
- overdue risks

payment KPIs:
- pending applications
- requested amount
- recommended amount
- approved amount
- paid amount

contractor KPI:
- contractor performance score

overall project status:
- cost_status
- schedule_status
- quality_status
- contractor_status
- risk_status

EXECUTIVE REPORTS

Create Report model:

- project
- reporting_period
- title
- status
- executive_summary
- recommendations
- published_at
- generated_by

The backend should be capable of generating a structured monthly executive report from project data.

Do not over-engineer PDF generation initially.

Create a report JSON representation first.

Later support PDF generation.

NOTIFICATIONS

Create Notification model.

Support:

- new payment application
- payment review completed
- variation submitted
- high-risk item
- overdue action
- inspection completed
- report published

API

Use RESTful APIs.

Suggested structure:

/api/auth/
/api/organizations/
/api/projects/
/api/projects/{id}/dashboard/
/api/projects/{id}/budget/
/api/projects/{id}/progress/
/api/projects/{id}/payments/
/api/projects/{id}/variations/
/api/projects/{id}/risks/
/api/projects/{id}/issues/
/api/projects/{id}/inspections/
/api/projects/{id}/documents/
/api/projects/{id}/reports/
/api/projects/{id}/contractors/
/api/notifications/
/api/audit/

API REQUIREMENTS

- Pagination
- Filtering
- Searching
- Ordering
- Validation
- Consistent error responses
- Permission checks
- Serializer validation
- API documentation

SECURITY

Implement:

- JWT authentication
- secure password handling
- permission checks
- organization isolation
- object-level permissions
- rate limiting where appropriate
- secure file handling
- CORS configuration
- CSRF where relevant
- production security settings
- no secrets in source code

Never trust organization/project IDs supplied by the frontend.

Validate ownership/access server-side.

SCALABILITY

Design for:

- hundreds of organizations
- thousands of projects
- millions of project records
- large numbers of documents/evidence files

Use:

- PostgreSQL indexes
- database constraints
- select_related/prefetch_related
- service-layer business logic
- asynchronous tasks for heavy processing
- object storage for files
- caching where appropriate

Do not prematurely introduce microservices.

Keep the MVP a modular monolith.

TESTING

Write tests for:

- authentication
- organization isolation
- permissions
- project creation
- budget calculations
- progress calculations
- payment workflow
- variation workflow
- risk scoring
- dashboard calculations
- audit logs

DEVELOPER EXPERIENCE

Provide:

- README
- .env.example
- Docker setup
- migrations
- seed/demo data
- API documentation
- test instructions
- clear project structure

Create demo data for:

Organization:
"GlintPM Private Demo"

Project:
"Luxury Residence — Lekki"

Project value:
₦500,000,000

Populate realistic demo:

- budget items
- progress updates
- payment applications
- variations
- risks
- milestones
- inspections
- evidence
- contractor performance

IMPORTANT PRODUCT PRINCIPLE

Do not turn this into a generic construction ERP.

The MVP's central question is:

"Can a high-value property owner understand the financial, schedule, execution and risk position of their project without being physically present?"

Build every API around answering that question.

Build the complete Django backend, database schema, APIs, authentication, permissions, calculations, tests and documentation.

Do not merely provide pseudocode.

Generate production-quality, maintainable code.


DJANGO BACKEND STRUCTURE

backend/
│
├── manage.py
│
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   │
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
│
├── apps/
│   │
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   ├── organizations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── tests/
│   │
│   ├── projects/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   └── tests/
│   │
│   ├── costs/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   ├── progress/
│   ├── payments/
│   ├── variations/
│   ├── risks/
│   ├── inspections/
│   ├── contractors/
│   ├── documents/
│   ├── reports/
│   ├── notifications/
│   └── audit/
│
├── common/
│   ├── models.py
│   ├── permissions.py
│   ├── pagination.py
│   ├── exceptions.py
│   ├── responses.py
│   └── utils.py
│
├── scripts/
│   └── seed_demo_data.py
│
├── tests/
│   ├── integration/
│   └── api/
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── pytest.ini


