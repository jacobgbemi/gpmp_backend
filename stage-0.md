You are building the backend foundation for GlintPM Private, a premium Owner-Side Project Control & Assurance platform.

GlintPM Private helps high-value property owners independently understand the financial, schedule, progress, payment and risk position of construction projects.

We are using:

- Python 3.12+
- Django 5.x
- Django REST Framework
- PostgreSQL
- JWT authentication using SimpleJWT
- django-environ
- django-cors-headers
- drf-spectacular
- pytest / pytest-django
- Ruff
- Docker-ready architecture

Use a modular monolith architecture.

IMPORTANT:
Follow this workflow strictly:

1. Define the business problem
2. Design the data model
3. Design the API
4. Implement the backend
5. Write tests
6. Test API with Postman
7. Build only the necessary frontend foundation
8. Test failure states
9. Check database integrity
10. Review security
11. Git commit
12. Document important decisions

========================================
1. BUSINESS PROBLEM
========================================

At this stage, GlintPM Private needs a clean, maintainable and secure backend foundation.

The foundation must support future domains such as:

- Organizations
- Projects
- Costs
- Progress
- Payments
- Variations
- Risks
- Inspections
- Documents
- Reports
- Notifications
- Audit logs

Do not implement these business domains yet.

========================================
2. DATA MODEL
========================================

Do not create business-domain models yet.

Create only the database/configuration foundation required by Django.

Do not prematurely create Project, Payment, Risk, Variation or other models.

========================================
3. API DESIGN
========================================

Create:

GET /api/health/

The endpoint should return a simple successful health response.

Prepare API documentation using drf-spectacular.

========================================
4. IMPLEMENTATION
========================================

Create this structure:

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

Use environment variables for secrets and environment-specific settings.

Configure:

- PostgreSQL
- DRF
- CORS
- JWT-ready authentication configuration
- OpenAPI documentation
- Logging
- timezone
- production security settings
- static/media configuration
- testing configuration

Create:

GET /api/health/

========================================
5. AUTOMATED TESTS
========================================

Write tests for:

- Django starts successfully
- health endpoint returns 200
- invalid configuration fails clearly
- API routing works
- database connection works

========================================
6. POSTMAN
========================================

Create a Postman collection:

GlintPM Private — Local

Add:

GET {{base_url}}/health/

Environment:

base_url = http://localhost:8000/api

Verify the endpoint manually.

========================================
7. FRONTEND
========================================

Do not build business functionality.

Only verify that the existing React/Vite frontend can eventually communicate with:

http://localhost:8000/api

Do not create Projects, Payments or Dashboard functionality.

========================================
8. FAILURE STATES
========================================

Test:

- Django unavailable
- PostgreSQL unavailable
- invalid environment variables
- invalid API path
- malformed request

========================================
9. DATABASE INTEGRITY
========================================

Verify:

- PostgreSQL connection
- migrations
- migration consistency
- no unexpected business tables
- no secrets stored in database

========================================
10. SECURITY REVIEW
========================================

Verify:

- DEBUG is environment controlled
- secrets are not hardcoded
- SECRET_KEY comes from environment
- database credentials come from environment
- CORS is configurable
- production settings are separated
- no sensitive information appears in logs

========================================
11. GIT
========================================

Create a clean commit:

feat(backend): establish project foundation

Do not commit:

- .env
- secrets
- local databases
- generated sensitive files

========================================
12. DOCUMENTATION
========================================

Update README with:

- architecture
- setup instructions
- environment variables
- how to run Django
- how to run tests
- how to run Ruff
- how to access API documentation
- Postman setup
- important architectural decisions

Do not proceed to Stage 1 until all checks pass.