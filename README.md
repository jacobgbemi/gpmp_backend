# GlintPM Private — Backend

Owner-side Project Control & Assurance platform for high-value construction
and property projects.

> **Stage 0 + Stage 1 scope.** Stage 0 established the Django project
> foundation (settings, Unfold admin, health check, OpenAPI docs, tooling).
> Stage 1 adds the multi-tenant security foundation: a custom email-based
> `User`, JWT authentication, `Organization` / `OrganizationMembership`,
> role-based permissions, and enforced organization isolation. Projects,
> Payments, Risks, Variations, Inspections, Documents, and Reports are still
> out of scope — they land in later stages.

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
  accounts/            # custom User, JWT login/refresh/me
    models.py           # User + UserManager (email login, UUID pk)
    serializers.py       # EmailTokenObtainPairSerializer, CurrentUserSerializer
    views.py             # LoginView, RefreshView, MeView
    admin.py              # Unfold-registered UserAdmin
    tests/
  organizations/       # Organization, OrganizationMembership, roles
    models.py            # Organization, OrganizationMembership, Role
    selectors.py          # read-side queries (organizations_for_user, ...)
    services.py           # write-side logic (create_organization, add_member, ...)
    permissions.py         # IsOrganizationMember, IsOrganizationAdminOrReadOnly
    views.py               # OrganizationViewSet
    admin.py                # Unfold-registered Organization/Membership admins
    tests/
common/
  models.py            # UUIDModel / TimeStampedModel / BaseModel
  permissions.py
  pagination.py
  exceptions.py        # consistent error envelope
  responses.py         # consistent success/error envelope
  utils.py
scripts/
  seed_demo_data.py     # placeholder until further business models exist
tests/
  test_project_setup.py # Django boot / admin / Unfold / OpenAPI / JWT config checks
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

## Stage 1 — Authentication & organization isolation

### Authentication architecture

- The login identifier is **email**, not username — `User.USERNAME_FIELD =
  "email"` and `username = None`. Email is stored lowercased and compared
  case-insensitively both in application code (`.lower()` on save/login) and
  at the database level, via a `UniqueConstraint(Lower("email"), ...)` — so
  `Alice@Example.com` and `alice@example.com` can never both register.
- Authentication is **stateless JWT** (`djangorestframework-simplejwt`), not
  server-side sessions, so the API can be called from the React SPA and,
  later, other clients without CSRF/session-cookie coupling. The Django
  admin (`/admin/`) still uses ordinary session auth — the two are
  independent and don't share tokens.
- `POST /api/auth/token/` accepts `{"email", "password"}` and returns an
  `{"access", "refresh"}` pair. `POST /api/auth/token/refresh/` exchanges a
  valid refresh token for a new access token. `GET /api/auth/me/` returns
  the authenticated user's profile plus their organization memberships.
- Passwords are hashed with Django's default password hasher (PBKDF2 by
  default); GlintPM never stores or logs plaintext passwords, and no
  serializer ever includes the `password` field in a response.

### Role definitions

Every `OrganizationMembership` carries exactly one role, scoped to that one
organization (a user can hold different roles in different organizations):

| Role | Intent |
|---|---|
| `PLATFORM_ADMIN` | GlintPM staff; cross-cutting admin capability, currently treated as an organization-admin-equivalent role |
| `ORGANIZATION_ADMIN` | Manages the organization itself: settings, membership, billing (later stages) |
| `PROJECT_MANAGER` | Owns delivery of one or more projects (later stages) |
| `PROJECT_CONTROLS` | Cost/schedule control specialist (later stages) |
| `SITE_INSPECTOR` | Field inspections and evidence capture (later stages) |
| `CONSULTANT` | External advisor with scoped, usually read-heavy access |
| `CLIENT_OWNER` | The paying client's own representative — assurance/oversight view |
| `VIEWER` | Read-only baseline access |

Only `PLATFORM_ADMIN` and `ORGANIZATION_ADMIN` are in `ADMIN_ROLES`
(`apps/organizations/models.py`) — the set permitted to modify organization
settings or manage members. Stage 1 defines all eight roles and enforces
the admin/non-admin split for organization mutation; per-role authorization
for future business domains (e.g. "only `SITE_INSPECTOR` can create an
inspection") is deferred to the stage that introduces that domain.

### Organization isolation strategy

The core guarantee: **a user can only ever see, in any API response, data
belonging to organizations they are a member of.** This is enforced at the
queryset level, not with post-hoc permission checks:

- `apps/organizations/selectors.py::organizations_for_user(user)` is the
  **only** queryset the `OrganizationViewSet` uses. It filters to
  `Organization.objects.filter(memberships__user=user)` — organizations the
  user doesn't belong to are simply absent from the queryset.
- Because DRF's generic views call `get_object()` against `get_queryset()`,
  requesting `/api/organizations/{foreign_id}/` doesn't find a permission
  failure — it finds **nothing**, and returns a plain `404`. A `403` would
  confirm the ID exists but is forbidden; a `404` reveals nothing. This is
  verified explicitly in `test_404_response_does_not_leak_org_b_existence`,
  which asserts a foreign-but-real org ID and a random UUID produce
  byte-identical 404 responses.
- The same selector backs `GET /api/auth/me/`'s `memberships` list, so a
  user's own profile never surfaces another organization's data either.
- Revoking a membership takes effect immediately on the next request —
  there's no cached authorization state — because every request re-runs the
  selector against the current database state.

### Permission strategy

Permission logic is centralized in `apps/organizations/permissions.py`
rather than scattered across views:

- `get_role(user, organization)` is the single source of truth for "what
  role does this user have in this organization" (or `None`).
- `IsOrganizationMember` — object-level check: is the requester a member at
  all.
- `IsOrganizationAdminOrReadOnly` — members can read (`GET`); only
  `ADMIN_ROLES` can write (`PATCH`). `OrganizationViewSet` uses this
  combined with `IsAuthenticated`, and disables `PUT`/`DELETE` entirely at
  the view level (`http_method_names`) since neither is part of the Stage 1
  API surface.
- Views never inline `if membership.role == ...` checks — they delegate to
  these permission classes, so the rule for "who can modify an
  organization" lives in exactly one place and every view enforcing it
  behaves identically.
- The backend never trusts an organization ID supplied by the client as
  proof of membership — every access re-derives membership from the
  database via `get_role`/the selector, not from anything in the request
  body or URL alone.

### JWT approach

- Library: `djangorestframework-simplejwt`, configured in
  `config/settings/base.py` under `SIMPLE_JWT`.
- **Access token lifetime**: 30 minutes by default (`ACCESS_TOKEN_LIFETIME_MINUTES`).
  Short-lived by design — a leaked access token has a small blast radius.
- **Refresh token lifetime**: 7 days by default (`REFRESH_TOKEN_LIFETIME_DAYS`).
- **Rotation + blacklisting**: `ROTATE_REFRESH_TOKENS = True` and
  `BLACKLIST_AFTER_ROTATION = True` — every refresh issues a new refresh
  token and immediately blacklists the one just used
  (`rest_framework_simplejwt.token_blacklist` is installed and migrated for
  this). A stolen refresh token can be used at most once before it's
  invalidated; `test_refresh_rotates_and_blacklists_old_token` proves the
  second use of an already-rotated token is rejected.
- The JWT claim carrying identity is `user_id`, set to the user's UUID
  (`USER_ID_FIELD = "id"`), never a sequential integer.
- Auth header: `Authorization: Bearer <access_token>`.

### Database constraints (Stage 1)

- `accounts_user_email_ci_unique` — case-insensitive unique constraint on
  `User.email` (`UniqueConstraint(Lower("email"), ...)`).
- `organizations_membership_user_org_unique` — unique constraint on
  `(user, organization)` on `OrganizationMembership`, enforced at the
  database level (not just in application code) — see
  `test_duplicate_membership_enforced_at_db_level`, which bypasses the
  service layer entirely and confirms the DB itself rejects the duplicate.
- `Organization.slug` is globally unique (`SlugField(unique=True)`); the
  `_unique_slug()` helper in `apps/organizations/services.py` appends a
  numeric suffix on collision rather than failing the request.
- Both `OrganizationMembership.user` and `.organization` use
  `on_delete=models.CASCADE` — a membership has no meaning without both
  sides, so deleting either party correctly removes the membership record
  rather than leaving an orphan or blocking the delete.
- An index on `(organization, role)` supports the common "who has role X in
  organization Y" query pattern used once role-gated business domains land.

### Postman workflow

Import both files from `postman/`:

- `GlintPM-Private-Local.postman_collection.json` — organized into **Auth**
  and **Organizations** folders, plus the Stage 0 health/schema requests.
- `GlintPM-Private-Local.postman_environment.json` — sets `base_url`,
  `user_email`, `user_password`, and empty placeholders for
  `access_token` / `refresh_token` / `organization_id` /
  `foreign_organization_id`.

Workflow:

1. Select the **GlintPM Private — Local** environment.
2. Run **Auth → Login**. Its test script automatically saves `access` and
   `refresh` into `{{access_token}}` / `{{refresh_token}}` — every other
   authenticated request uses `{{access_token}}` via Bearer auth, so you
   never paste a token by hand.
3. Run **Organizations → Create organization**; its test script saves the
   new `id` into `{{organization_id}}` for the requests that follow.
4. Run **Organizations → List / Retrieve / Update / List members** against
   that saved `organization_id`.
5. Run the negative-path requests to confirm failure states: **Login —
   invalid password** (401), **Current user — missing token** (401),
   **Retrieve organization — no token** (401). For the IDOR check
   (**Retrieve foreign organization**), manually set
   `foreign_organization_id` to an organization ID that belongs to a
   *different* logged-in user, and confirm it returns 404.

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

Follow the prompts for email and password (there's no username field — the
custom `User` model logs in with email only).

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

This validates, per the Stage 0 + Stage 1 checklist:

- Django starts and settings load cleanly
- the database connection works
- `/api/health/` responds correctly and is publicly accessible
- `/admin/` loads and Unfold is correctly installed/configured, with
  `User`, `Organization`, and `OrganizationMembership` registered
- no business-domain apps/tables have been prematurely introduced
- OpenAPI schema, Swagger UI, and ReDoc all load
- JWT settings (lifetimes, rotation, blacklisting) are configured as
  documented above
- user creation, login (incl. case-insensitive email, wrong password,
  unknown email, inactive user), token refresh (incl. rotation/blacklist,
  expired, malformed, missing), and `/me/` (incl. missing/expired/malformed
  token) all behave correctly
- organization creation (incl. creator-becomes-admin, unique slugs, mass
  assignment protection), membership creation, every role is assignable,
  duplicate membership is rejected both at the service layer and at the
  database level
- organization access is scoped to the user's own organizations, admin-only
  mutation is enforced, `PUT`/`DELETE` are disabled
- **explicit IDOR tests**: a user in Org A cannot retrieve, modify, or list
  members of Org B, Org B never appears in Org A's list or `/me/` response,
  a 404 for a real foreign org is indistinguishable from a 404 for a random
  UUID, and losing membership immediately revokes access
- cascade behavior and uniqueness constraints hold at the database level

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

See [Postman workflow](#postman-workflow) above for the full walkthrough.
Quick version: import both files from `postman/`, select the environment,
run **Auth → Login** first (it saves your tokens automatically), then run
whatever else you need.

## Security notes (Stage 0 + Stage 1)

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
- **Password hashing**: Django's default hasher (PBKDF2); no plaintext
  password is ever stored, logged, or returned in a response.
- **JWT handling**: short-lived access tokens (30 min default), rotating +
  blacklisted refresh tokens (7 day default) — see [JWT approach](#jwt-approach)
  above.
- **Object-level permissions**: every organization access goes through
  `apps/organizations/permissions.py`, never an inline role check in a view.
- **Organization isolation / IDOR**: enforced at the queryset level
  (`organizations_for_user`), not as an after-the-fact permission check —
  foreign organizations are invisible, not merely forbidden. Covered by an
  explicit IDOR test suite (`apps/organizations/tests/test_organizations.py::TestCrossOrganizationIDOR`).
- **Mass assignment**: `OrganizationSerializer` marks `id`, `slug`,
  `my_role`, `created_at`, `updated_at` read-only — only `name` is
  client-writable on create/update. Covered by
  `test_mass_assignment_of_slug_and_role_is_ignored`.
- **Serializer exposure / sensitive fields**: `CurrentUserSerializer`
  explicitly excludes `password`, `is_superuser`, `is_staff`, and any
  permission fields — it's an allow-list of fields (`fields = [...]`), not
  `fields = "__all__"` with exclusions.
- **Token expiration**: verified directly — expired access and refresh
  tokens are rejected (`test_me_with_expired_token_is_unauthorized`,
  `test_refresh_with_expired_token_fails`).
- Organization IDs supplied by the client are never trusted as proof of
  membership — every request re-derives the caller's role/membership from
  the database.

## Architectural decisions (Stage 0 + Stage 1)

1. **Settings are split by environment** (`base` / `development` /
   `production`) rather than a single `settings.py` with `if DEBUG:`
   branching, so production configuration can never accidentally inherit a
   development-only default.
2. **`apps/` vs `common/`** — `apps/` holds Django apps with URLs, views,
   models, and tests (`core` for the health check, `accounts` for identity,
   `organizations` for multi-tenancy). `common/` holds cross-cutting,
   non-app Python modules (base model classes, pagination, exception
   handling, response envelopes) that every business-domain app imports,
   without those modules themselves being an installable Django app.
3. **Consistent response envelope** — `common/responses.py` and
   `common/exceptions.py` establish `{"success", "message", "data"}` /
   `{"success", "message", "errors"}` shapes from the very first endpoint,
   so the React frontend's API client doesn't need special-casing per app
   later.
4. **UUID public identifiers** — every model inherits `UUIDModel` (directly
   or via `common.models.BaseModel`), so no sequential integer ID is ever
   exposed through the API — including `User.id`, which uses `UUIDModel`
   directly rather than `BaseModel` since Django's `AbstractUser` already
   supplies its own timestamp-adjacent fields (`date_joined`, `last_login`).
5. **Django Unfold configured and now used** — `User`, `Organization`, and
   `OrganizationMembership` are all Unfold-registered with tailored
   `list_display`, search, filters, and inline memberships, per the Stage 1
   requirement.
6. **Selectors/services split** (`apps/organizations/selectors.py` /
   `services.py`) — read-side queries (selectors) are kept separate from
   write-side business logic (services) so the "only see your own
   organizations" rule lives in exactly one queryset function that every
   read path shares, rather than being re-implemented per view.
7. **404, not 403, for cross-organization access** — a deliberate choice:
   returning 403 for a real-but-foreign organization ID would confirm that
   ID exists, enabling enumeration. Returning 404 (because the object
   simply isn't in the user's queryset) reveals nothing. This is why
   `OrganizationViewSet.get_queryset()` filters by membership rather than
   fetching-then-checking-permission.
8. **Custom `User` model from Stage 1** — introduced now (rather than
   retrofitted later, which is far more painful in Django since
   `AUTH_USER_MODEL` can't be changed after the first migration) with email
   as the login identifier per the product requirement, UUID primary key,
   and a manager that normalizes/lowercases email consistently.
9. **Refresh token rotation + blacklisting enabled by default** — accepted
   the extra `token_blacklist` table/migrations in Stage 1 because silently
   allowing indefinite refresh-token reuse is a bigger long-term risk than
   the added complexity.
10. **Celery wired, still unused** — `config/celery.py` and `CELERY_*`
    settings exist so `apps/*/tasks.py` auto-discovery works the moment
    background jobs are introduced, without a dependency on a running
    broker for tests.