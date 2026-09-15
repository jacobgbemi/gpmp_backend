Build Backend Stage 0 of GlintPM Private.

GlintPM Private is a premium Owner-Side Project Control & Assurance platform for high-value construction and property projects.

TECH STACK

- Python 3.12+
- Django 5.x
- Django REST Framework
- PostgreSQL
- Django Unfold
- SimpleJWT
- django-environ
- django-cors-headers
- drf-spectacular
- pytest / pytest-django
- Ruff
- Docker-ready architecture

Use a modular monolith.

==================================================
DEVELOPMENT WORKFLOW
==================================================

Follow this workflow strictly:

1. Define the business problem
2. Design the data model
3. Design the API
4. Implement backend
5. Write tests
6. Test API with Postman
7. Build frontend
8. Test failure states
9. Check database integrity
10. Review security/permissions
11. Git commit
12. Document important decisions

==================================================
1. BUSINESS PROBLEM
==================================================

Create the technical foundation for GlintPM Private.

The platform will eventually manage:

- organizations
- users
- projects
- budgets
- progress
- payments
- variations
- risks
- issues
- inspections
- evidence
- documents
- reports
- notifications
- decisions
- audit logs

Do not implement these business domains yet.

However, Django Unfold must be installed and configured from the beginning because it will serve as the internal administration/back-office interface.

The React application will remain the primary user-facing application.

==================================================
2. DATA MODEL
==================================================

Do not create business-domain models yet.

Only create the Django foundation required for the project.

Do not prematurely create:

- Project
- Payment
- Risk
- Variation
- Inspection
- Document
- Report

==================================================
3. API
==================================================

Create:

GET /api/health/

Return a simple health response.

Configure drf-spectacular/OpenAPI.

==================================================
4. BACKEND IMPLEMENTATION
==================================================

Create:

backend/
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
├── common/
├── scripts/
├── tests/
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── Dockerfile
├── .env.example
├── pytest.ini
└── README.md

Configure Django Unfold.

In INSTALLED_APPS:

"unfold"

must appear before:

"django.contrib.admin"

Configure:

UNFOLD = {
    "SITE_TITLE": "GlintPM Private",
    "SITE_HEADER": "GlintPM Private",
    "SITE_SYMBOL": "shield",
}

Keep the default Django admin URL:

/admin/

Do not build custom admin dashboards yet.

Do not add business models to the admin yet.

==================================================
5. TESTS
==================================================

Test:

- Django starts
- database connection
- health endpoint
- admin URL loads
- Unfold loads successfully
- no configuration errors
- OpenAPI documentation loads

==================================================
6. POSTMAN
==================================================

Create:

GlintPM Private — Local

Environment:

base_url = http://localhost:8000/api

Test:

GET {{base_url}}/health/

Also verify the admin separately in the browser:

http://localhost:8000/admin/

==================================================
7. FRONTEND
==================================================

Do not build business functionality.

Only verify that the React frontend can communicate with:

http://localhost:8000/api

The Django admin is an internal backend interface and should NOT be recreated in React.

==================================================
8. FAILURE STATES
==================================================

Test:

- PostgreSQL unavailable
- Django unavailable
- invalid environment variables
- invalid API endpoint
- admin unavailable
- incorrect configuration

==================================================
9. DATABASE INTEGRITY
==================================================

Verify:

- migrations
- database connection
- migration consistency
- no premature business tables
- Django admin authentication tables are correct

==================================================
10. SECURITY
==================================================

Review:

- DEBUG
- SECRET_KEY
- database credentials
- CORS
- admin authentication
- environment variables
- production settings

Do not expose secrets.

Do not create custom admin authentication bypasses.

==================================================
11. GIT
==================================================

Commit:

feat(backend): establish backend foundation with Unfold admin

==================================================
12. DOCUMENTATION
==================================================

Document:

- backend architecture
- Django Unfold purpose
- admin setup
- environment variables
- how to create a superuser
- how to run Django
- how to run tests
- how to run Ruff
- Postman setup
- API documentation
- important architectural decisions

IMPORTANT:

Django Unfold is the internal administration/back-office layer.

React is the primary user-facing application.

Do not duplicate Django admin functionality in React unless there is a specific product requirement.