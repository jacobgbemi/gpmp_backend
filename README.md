# GlintPM Private — Backend

Owner-side Project Control & Assurance platform for high-value construction
and property projects.

> **Stage 0 scope.** This is the Django project foundation only: settings,
> Unfold admin, health check, OpenAPI docs, tests, and tooling. No
> business-domain models (Organization, Project, Payment, Risk, ...) exist
> yet — they land in later stages.

## Architecture at a glance

- **Modular monolith** — Django REST Framework, one deployable service,
  business logic split into `apps/*` as they're introduced.
- **PostgreSQL** as the database, configured via `DATABASE_URL`.
- **Django Unfold** as the internal administration / back-office interface,
  served at `/admin/`. It is *not* rebuilt in React — the React app is the
  user-facing product; Unfold is for internal ops only.
- **JWT auth** (SimpleJWT) for the API.
- **drf-spectacular** for OpenAPI schema + Swagger/ReDoc docs.
- Environment-specific settings under `config/settings/` (`base.py`,
  `development.py`, `production.py`) — nothing environment-specific is
  hardcoded into a single `settings.py`.

## Project layout

```
config/
  settings/
    base.py          # shared settings
    development.py    # local overrides (permissive defaults)
    production.py     # strict, no insecure fallbacks
  celery.py            # Celery app (task modules land in a later stage)
  urls.py
  asgi.py / wsgi.py
apps/
  core/                # health check + non-business-domain endpoints
common/
  models.py            # UUIDModel / TimeStampedModel / BaseModel
  permissions.py
  pagination.py
  exceptions.py        # consistent error envelope
  responses.py         # consistent success/error envelope
  utils.py
scripts/
  seed_demo_data.py     # placeholder until business models exist
tests/
  test_project_setup.py # Django boot / admin / Unfold / OpenAPI checks
requirements/
  base.txt / development.txt / production.txt
postman/
  GlintPM-Private-Local.postman_collection.json
  GlintPM-Private-Local.postman_environment.json
Dockerfile
.env.example
pytest.ini
```

## Why Django Unfold

Unfold replaces the default Django admin styling/UX and is registered
**before** `django.contrib.admin` in `INSTALLED_APPS` so it can override the
default admin templates. It's configured from Stage 0 onward because it will
be the primary internal tool for ops/back-office staff to inspect and manage
data as business-domain apps are added — it is intentionally *not* wired to
any business models yet.

Configuration lives in `config/settings/base.py`:

```python
UNFOLD = {
    "SITE_TITLE": "GlintPM Private",
    "SITE_HEADER": "GlintPM Private",
    "SITE_SYMBOL": "shield",
}
```

The admin URL stays at the Django default: `/admin/`.

## Environment variables

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable | Purpose | Dev default |
|---|---|---|
| `SECRET_KEY` | Django secret key | insecure local-only fallback in dev; **required, no fallback** in production |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1,0.0.0.0` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://glintpm:glintpm@localhost:5432/glintpm` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins allowed to call the API | `http://localhost:3000` |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime | `30` |
| `REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token lifetime | `7` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis URLs | `redis://localhost:6379/0` |

Production (`config/settings/production.py`) deliberately has **no**
fallback for `SECRET_KEY` or `ALLOWED_HOSTS` — the process refuses to start
if they're missing, rather than silently running insecurely.

## Running locally

### 1. Prerequisites

- Python 3.12+
- PostgreSQL running locally (or via Docker — see below)

### 2. Set up a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` if your local PostgreSQL credentials differ from the default.

### 4. Create the database

```bash
createdb glintpm   # or: psql -c "CREATE DATABASE glintpm;"
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (for `/admin/`)

```bash
python manage.py createsuperuser
```

Follow the prompts for email/username and password.

### 7. Run the development server

```bash
python manage.py runserver
```

- API health check: http://localhost:8000/api/health/
- Django Unfold admin: http://localhost:8000/admin/
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Raw OpenAPI schema: http://localhost:8000/api/schema/

## Running with Docker

```bash
docker build -t glintpm-backend .
docker run --env-file .env -p 8000:8000 glintpm-backend
```

The container runs `gunicorn` against `config.settings.production` — make
sure `.env` has production-appropriate values (a real `SECRET_KEY`,
`ALLOWED_HOSTS`, `DATABASE_URL` pointing at a reachable PostgreSQL instance)
before using it outside local testing.

## Running tests

```bash
pytest
```

This validates, per the Stage 0 checklist:

- Django starts and settings load cleanly
- the database connection works
- `/api/health/` responds correctly and is publicly accessible
- `/admin/` loads and Unfold is correctly installed/configured
- no business-domain apps/tables have been prematurely introduced
- OpenAPI schema, Swagger UI, and ReDoc all load

Run with coverage:

```bash
coverage run -m pytest
coverage report
```

## Linting

```bash
ruff check .
ruff format .
```

## API documentation

OpenAPI schema generation is powered by `drf-spectacular`, configured in
`config/settings/base.py` under `SPECTACULAR_SETTINGS`. Browse it at
`/api/docs/` (Swagger) or `/api/redoc/` (ReDoc) while the server is running.

## Postman

Import both files from `postman/`:

- `GlintPM-Private-Local.postman_collection.json`
- `GlintPM-Private-Local.postman_environment.json`

The environment sets `base_url = http://localhost:8000/api`. Select the
environment in Postman, then run the **Health Check** request. Verify the
admin separately in a browser at `http://localhost:8000/admin/` (Postman is
not used for the Django admin UI, which relies on session auth + HTML forms).

## Security notes (Stage 0)

- `SECRET_KEY` and `ALLOWED_HOSTS` have **no fallback** in production —
  missing them fails fast at startup instead of running insecurely.
- `DEBUG=False` is enforced in `config/settings/production.py` regardless of
  environment variable content.
- CORS is explicit allow-list only (`CORS_ALLOWED_ORIGINS`), never wildcard.
- No secrets are committed to source control — `.env` is git-ignored;
  `.env.example` documents required variables without real values.
- Production enables HSTS, secure cookies, SSL redirect, and disables the
  browsable-schema exposure that's convenient in development
  (`SPECTACULAR_SETTINGS["SERVE_INCLUDE_SCHEMA"]`).
- No custom admin authentication bypass exists — `/admin/` uses Django's
  standard session-based auth exactly as Unfold expects it.

## Architectural decisions (Stage 0)

1. **Settings are split by environment** (`base` / `development` /
   `production`) rather than a single `settings.py` with `if DEBUG:`
   branching, so production configuration can never accidentally inherit a
   development-only default.
2. **`apps/` vs `common/`** — `apps/` holds Django apps with URLs, views,
   models, and tests (currently only `core`, for the health check).
   `common/` holds cross-cutting, non-app Python modules (base model
   classes, pagination, exception handling, response envelopes) that every
   future business-domain app will import, without those modules themselves
   being an installable Django app.
3. **Consistent response envelope** — `common/responses.py` and
   `common/exceptions.py` establish `{"success", "message", "data"}` /
   `{"success", "message", "errors"}` shapes from the very first endpoint,
   so the React frontend's API client doesn't need special-casing per app
   later.
4. **UUID public identifiers** — `common/models.py` defines `UUIDModel` /
   `TimeStampedModel` / `BaseModel` now, even though no concrete models use
   them yet, so every future business-domain model has a ready-made,
   consistent base to inherit from.
5. **Django Unfold configured but not customized** — installed and themed
   (title/header/symbol) from the start per the requirement, but no
   `ModelAdmin` customization happens until real models exist to administer.
6. **No custom `User` model yet** — Stage 0 explicitly avoids business
   domains, and a custom user model is an `accounts` app concern for a
   later stage; Django's default `auth.User` is used for now so
   `createsuperuser` works out of the box.
7. **Celery wired, unused** — `config/celery.py` and `CELERY_*` settings
   exist so `apps/*/tasks.py` auto-discovery works the moment background
   jobs are introduced, without a Stage 0 dependency on a running broker
   for tests (Celery eager/broker connectivity isn't exercised by any test).