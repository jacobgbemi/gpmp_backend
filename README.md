# GlintPM Private — Backend

Owner-side Project Control & Assurance platform for high-value construction
and property projects.

> **Stage 0 + Stage 1 + Stage 2 scope.** Stage 0 established the Django
> project foundation (settings, Unfold admin, health check, OpenAPI docs,
> tooling). Stage 1 added the multi-tenant security foundation: a custom
> email-based `User`, JWT authentication, `Organization` /
> `OrganizationMembership`, role-based permissions, and enforced
> organization isolation. Stage 2 establishes the financial and progress
> truth of a project: `Project`, `ProjectBudget`/`BudgetItem`,
> `ProgressUpdate`, and `PaymentApplication`, with a payment review state
> machine and an owner-facing dashboard. Variations, Risks, Issues,
> Inspections, Documents, Reports, and Notifications are still out of
> scope — they land in later stages.

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
  projects/            # Project, ProjectBudget, BudgetItem, ProgressUpdate,
                        # PaymentApplication — the financial/progress truth
    models.py            # status/transition tables live alongside the models
    selectors.py          # projects_for_user, project_dashboard, ...
    services.py            # create_project, PaymentService.review(), ...
    permissions.py          # PROJECT_WRITE_ROLES, PAYMENT_REVIEW_ROLES
    serializers.py           # Project/Budget/Progress/Payment/Dashboard
    views.py                  # ProjectViewSet (+ budget/progress/payments/
                               # dashboard sub-actions), PaymentViewSet
    admin.py                   # Unfold-registered admins for all 5 models
    tests/
common/
  models.py            # UUIDModel / TimeStampedModel / BaseModel
  validators.py        # MONEY_VALIDATORS / PERCENT_VALIDATORS
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

## Stage 2 — Financial & progress truth

### Financial data model

```
Organization
  └── Project (organization FK, PROTECT)
        ├── ProjectBudget (one-to-one)
        │     └── BudgetItem (many) — category, original/approved/committed/actual
        ├── ProgressUpdate (many, immutable) — one per reporting_date
        └── PaymentApplication (many) — requested/recommended/approved/paid
```

- Every `Project` belongs to exactly one `Organization` (`on_delete=PROTECT`
  — an organization cannot be deleted out from under its projects). Every
  `ProjectBudget`, `BudgetItem`, `ProgressUpdate`, and `PaymentApplication`
  traces back to a `Project` (`on_delete=CASCADE` for the leaves — they only
  have meaning attached to their project). It is not possible for a
  `PaymentApplication` (or any of these) to exist without a valid project:
  the foreign key is required (`null=False`), enforced at the database
  level, and `test_no_payment_can_exist_without_a_project` asserts this
  directly.
- Money is always `DecimalField` (never `float`), validated non-negative
  via `common.validators.MONEY_VALIDATORS` — see "money precision" below.
- `ProjectBudget` stores no totals of its own. Every total
  (`original_total`, `approved_total`, etc.) is computed on read from its
  `BudgetItem` rows (`apps.projects.selectors._budget_totals`), so a
  cached total can never drift out of sync with its line items.
- `ProgressUpdate` is immutable: the API only ever lists and creates these
  (`ProjectViewSet.progress` supports GET/POST only) — there is no
  update or delete endpoint, so a project's progress history can always be
  trusted and replayed. One update per `(project, reporting_date)` is
  enforced by a database `UniqueConstraint`.

### Payment lifecycle

`PaymentApplication.status` moves through a strict state machine, enforced
entirely in `PaymentService.review()` (`apps/projects/services.py`) — views
never set `.status` directly:

```
SUBMITTED → UNDER_REVIEW → RECOMMENDED → APPROVED → PARTIALLY_PAID → PAID
    │             │              │
    └─────────────┴──────────────┴──────────────────────────→ REJECTED
```

Each transition is one `POST /api/payments/{id}/review/` call with a
`decision`:

| Decision | Legal from | Effect |
|---|---|---|
| `START_REVIEW` | `SUBMITTED` | → `UNDER_REVIEW` |
| `RECOMMEND` | `UNDER_REVIEW` | sets `amount_recommended` (≤ `amount_requested`) → `RECOMMENDED` |
| `APPROVE` | `RECOMMENDED` | sets `amount_approved` (≤ `amount_recommended`) → `APPROVED` |
| `REJECT` | `SUBMITTED`, `UNDER_REVIEW`, `RECOMMENDED` | requires `notes` → `REJECTED` (terminal) |
| `RECORD_PAYMENT` | `APPROVED`, `PARTIALLY_PAID` | adds to `amount_paid` (cumulative total ≤ `amount_approved`) → `PARTIALLY_PAID` or `PAID` once fully paid |

A payment is created directly as `SUBMITTED` (there is no separate "submit
draft" step in the Stage 2 API surface — `DRAFT` remains in the status
choices for schema completeness but isn't reachable via the API today).
`PAID` and `REJECTED` are terminal — no further transitions are legal, and
every illegal transition (skipping a step, acting on a terminal payment,
an unknown `decision`) returns `400` with a specific message, never a
silent no-op. `RECORD_PAYMENT` supports partial payments: each call adds
to the running `amount_paid` total, moving to `PARTIALLY_PAID` until the
cumulative total reaches `amount_approved`, at which point it becomes
`PAID` automatically.

### Why requested/recommended/approved/paid are separate

This is the core feature of the payments domain, not an implementation
detail. Four independent `DecimalField`s, never collapsed into one
"amount":

- **`amount_requested`** — what the contractor asked for. Set once, at
  submission, and never changed afterward — it's the historical record of
  the original request.
- **`amount_recommended`** — what GlintPM's technical review determined is
  actually justified (may be less than requested, e.g. after a measured
  quantities check). This is GlintPM's independent assurance function —
  the entire product proposition depends on this number being visibly
  distinct from what was merely asked for.
- **`amount_approved`** — what the organization's decision-maker actually
  authorized for payment, which may differ from the recommendation for
  reasons outside GlintPM's technical assessment (cash flow, disputes,
  partial authorization).
- **`amount_paid`** — what has actually left the bank, which may lag
  behind approval and may arrive in more than one instalment
  (`PARTIALLY_PAID`).

Collapsing these into one field would silently destroy the owner's ability
to see, at a glance, the gap between "asked for" and "actually justified"
and between "authorized" and "actually paid" — which is precisely the
information asymmetry GlintPM exists to close (see "Business problem" in
`stage-2.md`). Every payment serializer response includes all four,
always, whether or not they're yet populated (`null` until that stage of
review is reached).

### Dashboard calculation rules

`GET /api/projects/{id}/dashboard/` (`apps.projects.selectors.project_dashboard`):

| Field | Formula |
|---|---|
| `original_budget` | Σ `BudgetItem.original_amount` |
| `approved_budget` | Σ `BudgetItem.approved_amount` |
| `actual_spend` | Σ `BudgetItem.actual_amount` |
| `committed_cost` | Σ `BudgetItem.committed_amount` |
| `forecast_final_cost` | `actual_spend + committed_cost` |
| `cost_variance` | `approved_budget - forecast_final_cost` (positive = under budget, negative = over budget) |
| `planned_progress_percent` | latest `ProgressUpdate.planned_progress_percent` by `reporting_date` |
| `actual_progress_percent` | latest `ProgressUpdate.actual_progress_percent` |
| `schedule_variance` | `actual_progress_percent - planned_progress_percent` (positive = ahead, negative = behind) |
| `pending_payments_count` / `_total` | payments still in `SUBMITTED`, `UNDER_REVIEW`, or `RECOMMENDED` (i.e. not yet a final decision) |
| `as_of_reporting_date` | `reporting_date` of the progress update the progress figures came from, or `null` if none exist |

`forecast_final_cost` deliberately does **not** include `original_budget`
or `approved_budget` — it answers "what will this project actually cost",
which is a function of money already spent plus money already committed,
not of what was originally planned. All figures are `0.00` (never an
error or `null`) on a brand-new project with no budget items or progress
yet, except `as_of_reporting_date`, which is `null` until a progress
update exists — there is no progress date to report.

### Progress calculation approach

`ProgressUpdate` stores exactly what was reported for a given
`reporting_date` — `planned_progress_percent` and
`actual_progress_percent`, both bounded `0`–`100` via
`common.validators.PERCENT_VALIDATORS`. The API also returns
`progress_variance_percent` (`actual - planned`) per update, computed at
serialization time, not stored — so a variance value is never at risk of
going stale relative to the two percentages it's derived from. The
dashboard's progress figures always come from the single most recent
`reporting_date` (`selectors.latest_progress_update`) — Stage 2
deliberately does not attempt trend analysis, S-curve fitting, or
schedule-engine-style forecasting; GlintPM stores summary progress
information rather than becoming a scheduling engine (see
`main-prompt.md`).

### Permission rules

- **`PROJECT_WRITE_ROLES`** (`PLATFORM_ADMIN`, `ORGANIZATION_ADMIN`,
  `PROJECT_MANAGER`, `PROJECT_CONTROLS`) — required to create/update/delete
  a project, add a budget item, or submit a progress update or payment
  application. Every other role (`SITE_INSPECTOR`, `CONSULTANT`,
  `CLIENT_OWNER`, `VIEWER`) has read-only access to a project it belongs
  to.
- **`PAYMENT_REVIEW_ROLES`** (`PLATFORM_ADMIN`, `ORGANIZATION_ADMIN`,
  `PROJECT_CONTROLS`) — a strictly narrower set used only for
  `POST /api/payments/{id}/review/`. **`PROJECT_MANAGER` is deliberately
  excluded** — separation of duties: the person managing delivery of a
  project should not also be the one recommending or approving its
  payments. `test_project_manager_cannot_review_payments` covers this
  directly.
- All permission checks resolve the requester's role via their live
  `OrganizationMembership` on the project's organization
  (`apps.projects.permissions.get_project_role`) — never from anything the
  client supplied in the request.
- A project (or anything nested under it — budget, progress, payments,
  dashboard) belonging to an organization the requester isn't a member of
  is absent from every queryset entirely (`selectors.projects_for_user`,
  `selectors.payment_queryset_for_user`), so it 404s — never 403. This
  matches the Stage 1 organization-isolation strategy exactly; Stage 2
  introduces no new isolation mechanism, it just extends the same one down
  through projects, budgets, progress, and payments.

### API examples

**Create a project:**
```
POST /api/projects/
{
  "organization": "f814813d-f1ba-4b7e-9d66-4fc65cd9f7e7",
  "name": "Lekki Residence",
  "project_code": "LEK-001",
  "project_type": "RESIDENTIAL",
  "contract_value": "500000000.00",
  "currency": "NGN"
}
→ 201 { "id": "...", "status": "PLANNING", ... }
```

**Add a budget line item, then read totals:**
```
POST /api/projects/{id}/budget/
{ "category": "CIVIL", "description": "Foundation works",
  "original_amount": "100000000.00", "approved_amount": "100000000.00",
  "committed_amount": "60000000.00", "actual_amount": "40000000.00" }

GET /api/projects/{id}/budget/
→ { "items": [...], "original_total": "100000000.00", ... }
```

**Move a payment through review:**
```
POST /api/payments/{id}/review/  { "decision": "START_REVIEW" }
POST /api/payments/{id}/review/  { "decision": "RECOMMEND", "amount": "18000000.00" }
POST /api/payments/{id}/review/  { "decision": "APPROVE", "amount": "18000000.00" }
POST /api/payments/{id}/review/  { "decision": "RECORD_PAYMENT", "amount": "18000000.00" }
→ final response: "status": "PAID", "amount_paid": "18000000.00"
```

**Retrieve the dashboard:**
```
GET /api/projects/{id}/dashboard/
→ {
    "original_budget": "500000000.00", "approved_budget": "480000000.00",
    "actual_spend": "180000000.00", "committed_cost": "150000000.00",
    "forecast_final_cost": "330000000.00", "cost_variance": "150000000.00",
    "planned_progress_percent": "45.00", "actual_progress_percent": "38.00",
    "schedule_variance": "-7.00",
    "pending_payments_count": 1, "pending_payments_total": "25000000.00",
    "as_of_reporting_date": "2026-06-01"
  }
```

### Postman workflow (Stage 2 additions)

The same collection now includes a **Projects (Stage 2)** folder covering
the full requested workflow — Login → Create organization → Create project
→ Create budget → Add progress update → Create payment → Review payment →
Retrieve dashboard — plus a **Projects — failure states** folder covering
401 (no token), 404 (invalid ID / wrong organization), and 400 (invalid
payload, negative amounts, duplicate project code, invalid status/payment
transitions). New environment variables: `project_id` and `payment_id` are
set automatically by the Stage 2 requests' test scripts; set
`foreign_project_id` / `foreign_payment_id` manually to a project/payment
ID that belongs to a *different* organization to exercise the IDOR checks
in the failure-states folder.

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

This validates, per the Stage 0 + Stage 1 + Stage 2 checklist:

- Django starts and settings load cleanly
- the database connection works
- `/api/health/` responds correctly and is publicly accessible
- `/admin/` loads and Unfold is correctly installed/configured, with
  `User`, `Organization`, `OrganizationMembership`, `Project`,
  `ProjectBudget`, `BudgetItem`, `ProgressUpdate`, and
  `PaymentApplication` all registered
- no business-domain apps/tables beyond accounts/organizations/projects
  have been prematurely introduced
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
- **project CRUD**, role-gated create/update/delete, status-transition
  validation (including terminal states), date-range validation, duplicate
  project-code rejection (per-organization, not global), and mass-assignment
  protection (`status` fixed at `PLANNING` on create, `organization`
  immutable after creation)
- **budget items and totals**: multi-item sums, zero-item defaults,
  negative-amount rejection, and cent-exact `Decimal` precision (no
  floating-point drift)
- **progress history**: immutability (no update/delete endpoint), duplicate
  `reporting_date` rejection, `0`–`100` boundary validation, and correct
  most-recent-first ordering
- **payment creation and the full review state machine**: every legal
  transition, every illegal transition (skipping steps, acting on a
  terminal payment, an unknown decision), the
  requested/recommended/approved/paid distinction staying genuinely
  independent, partial payments accumulating correctly to `PAID`, and
  **`PROJECT_MANAGER` being blocked from reviewing payments** (separation
  of duties)
- **dashboard calculations** against a realistic ₦500M-scale financial
  scenario, plus edge cases (no data, over-budget, ahead-of-schedule)
- **organization isolation extends through every Stage 2 resource** —
  project, budget, progress, and payment access are all confirmed to 404
  (never 403) across organizations, including at the review action

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

See [Postman workflow](#postman-workflow) and
[Postman workflow (Stage 2 additions)](#postman-workflow-stage-2-additions)
above for the full walkthrough. Quick version: import both files from
`postman/`, select the environment, run **Auth → Login** first (it saves
your tokens automatically), then **Organizations → Create organization**,
then work through the **Projects (Stage 2)** folder top to bottom.

## Security notes (Stage 0 + Stage 1 + Stage 2)

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
  `apps/organizations/permissions.py`, never an inline role check in a view;
  every project/budget/progress/payment access goes through
  `apps/projects/permissions.py` on the same principle.
- **Organization isolation / IDOR**: enforced at the queryset level
  (`organizations_for_user`, and in Stage 2 `projects_for_user` /
  `payment_queryset_for_user`), not as an after-the-fact permission check —
  foreign organizations, projects, and payments are invisible, not merely
  forbidden. Covered by explicit IDOR test suites in both
  `apps/organizations/tests/test_organizations.py::TestCrossOrganizationIDOR`
  and `apps/projects/tests/test_projects.py::TestProjectOrganizationIsolation`
  / `apps/projects/tests/test_payments.py::TestPaymentIsolation`.
- **Mass assignment**: `OrganizationSerializer` marks `id`, `slug`,
  `my_role`, `created_at`, `updated_at` read-only — only `name` is
  client-writable on create/update (`test_mass_assignment_of_slug_and_role_is_ignored`).
  `ProjectSerializer` fixes `status` at `PLANNING` on create (a client
  cannot create a project that's already `COMPLETED`) and makes
  `organization` immutable after creation
  (`test_status_cannot_be_set_directly_on_create`,
  `test_organization_is_immutable_after_creation`). `PaymentApplication`'s
  `amount_recommended`/`amount_approved`/`amount_paid`/`status` are
  read-only on the serializer entirely — they can only change through
  `PaymentService.review()`, never a direct field write.
- **Payment authorization / separation of duties**: `PAYMENT_REVIEW_ROLES`
  deliberately excludes `PROJECT_MANAGER` — the role that can create and
  manage a project is not the role permitted to recommend or approve its
  payments. Verified by `test_project_manager_cannot_review_payments`.
- **Serializer exposure / sensitive fields**: `CurrentUserSerializer`
  explicitly excludes `password`, `is_superuser`, `is_staff`, and any
  permission fields — it's an allow-list of fields (`fields = [...]`), not
  `fields = "__all__"` with exclusions.
- **Token expiration**: verified directly — expired access and refresh
  tokens are rejected (`test_me_with_expired_token_is_unauthorized`,
  `test_refresh_with_expired_token_fails`).
- Organization and project IDs supplied by the client are never trusted as
  proof of membership or access — every request re-derives the caller's
  role/membership from the database
  (`apps.projects.permissions.get_project_role`).

## Architectural decisions (Stage 0 + Stage 1 + Stage 2)

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
11. **`PROTECT` at the org→project boundary, `CASCADE` below it** —
    `Project.organization` uses `on_delete=PROTECT` (an organization must
    not silently take its financial history down with it, even though
    there's no organization-delete endpoint today — the constraint
    documents intent for when one exists). Everything nested under a
    project (`ProjectBudget`, `BudgetItem`, `ProgressUpdate`,
    `PaymentApplication`) uses `CASCADE`, because none of those records
    have meaning independent of their project.
12. **Budget totals are always computed, never stored** — `ProjectBudget`
    has no total fields; `apps.projects.selectors._budget_totals` sums
    `BudgetItem` rows on every read. A stored, cached total could drift
    out of sync with an edited or added line item; a computed one cannot.
13. **`PaymentService.review()` as an explicit state machine** — rather
    than a generic `PATCH /api/payments/{id}/` that lets a client set
    `status` directly, every transition is a named `decision` validated
    against `PAYMENT_STATUS_TRANSITIONS`. This makes illegal transitions
    (approve before recommend, review a paid payment) impossible to reach
    by construction, not just by convention, and keeps the four money
    fields' business rules (recommended ≤ requested, approved ≤
    recommended, cumulative paid ≤ approved) in one auditable place.
14. **Payment review roles are narrower than project write roles** —
    `PROJECT_WRITE_ROLES` (who can create/manage a project) and
    `PAYMENT_REVIEW_ROLES` (who can review its payments) are two distinct
    sets, not one. `PROJECT_MANAGER` is deliberately excluded from the
    latter as a separation-of-duties control, even though it's included in
    the former.
15. **Progress updates have no update/delete endpoint** — immutability is
    enforced by what the `ProjectViewSet.progress` action supports (GET,
    POST only), not by a soft convention. A project's progress history can
    always be trusted precisely because nothing in the API can rewrite it.
16. **`ProjectSerializer` flips which field is read-only based on whether
    it's creating or updating** — `organization` is writable (and
    queryset-restricted to the requester's own orgs) only on create, then
    permanently read-only; `status` is read-only on create (always starts
    `PLANNING`) but writable on update, where `services.update_project`
    validates the transition. Both directions of this — writable-then-locked
    and locked-then-writable — are defense against mass assignment, just
    applied to different fields at different times in a project's life.