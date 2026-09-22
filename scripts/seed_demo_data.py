"""
Demo data seed script.

Creates one realistic organization/project so the API and frontend have
something to show without a person having to click it all together by
hand. Every record goes through the same services/selectors the API
itself uses (apps.accounts, apps.organizations.services,
apps.projects.services, apps.projects.selectors) — nothing here writes
directly to a model that has a service, so the seeded data obeys the
same validation and status-transition rules real requests do.

Idempotent: safe to run more than once. If the demo organization already
has the demo project, the script prints a message and exits without
creating duplicates or re-running the payment workflow.

Creates:
    - User:          demo@glintpm.dev (password: DemoPass123!)
    - Organization:  "GlintPM Private Demo", with that user as
                      ORGANIZATION_ADMIN
    - Project:       "Luxury Residence — Lekki" (LRL-001, NGN
                      500,000,000, ESTATE_DEVELOPMENT, ACTIVE)
    - ProjectBudget with 7 BudgetItems across the standard categories
    - 4 ProgressUpdates (historical, monthly, actual trailing plan)
    - 5 PaymentApplications, one per point in the review lifecycle:
      SUBMITTED, UNDER_REVIEW, RECOMMENDED, REJECTED, and one carried
      all the way through to PARTIALLY_PAID.

Run with:
    python manage.py shell -c "import scripts.seed_demo_data as s; s.run()"
"""

from datetime import date
from decimal import Decimal

from apps.accounts.models import User
from apps.organizations import services as org_services
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects import services as project_services
from apps.projects.models import Project, ProjectType

DEMO_USER_EMAIL = "demo@glintpm.dev"
DEMO_USER_PASSWORD = "DemoPass123!"  # noqa: S105 - throwaway local demo credential

ORGANIZATION_NAME = "GlintPM Private Demo"
PROJECT_CODE = "LRL-001"

# (category, code, description, original, approved, committed, actual)
BUDGET_ITEMS = [
    (
        "CIVIL",
        "C-01",
        "Substructure & foundations",
        "60000000.00",
        "62000000.00",
        "58000000.00",
        "55000000.00",
    ),
    (
        "STRUCTURAL",
        "S-01",
        "Superstructure frame",
        "95000000.00",
        "98000000.00",
        "90000000.00",
        "78000000.00",
    ),
    (
        "ARCHITECTURAL",
        "A-01",
        "Envelope & roofing",
        "45000000.00",
        "45000000.00",
        "40000000.00",
        "22000000.00",
    ),
    (
        "MEP",
        "M-01",
        "Mechanical, electrical & plumbing",
        "70000000.00",
        "73000000.00",
        "65000000.00",
        "31000000.00",
    ),
    (
        "FINISHES",
        "F-01",
        "Interior finishes & fittings",
        "80000000.00",
        "85000000.00",
        "40000000.00",
        "9000000.50",
    ),
    (
        "EXTERNAL_WORKS",
        "E-01",
        "Landscaping & external works",
        "18000000.00",
        "18000000.00",
        "5000000.00",
        "0.00",
    ),
    (
        "PROFESSIONAL_FEES",
        "P-01",
        "Design, PM & consultancy fees",
        "22000000.00",
        "24000000.00",
        "22000000.00",
        "15000000.00",
    ),
]

# (reporting_date, planned_percent, actual_percent, notes)
PROGRESS_UPDATES = [
    (
        date(2026, 6, 30),
        "20.00",
        "18.00",
        "Foundation works underway; minor delay clearing site access.",
    ),
    (
        date(2026, 7, 31),
        "38.00",
        "33.00",
        "Substructure complete. Rebar shortage slowed frame start.",
    ),
    (
        date(2026, 8, 31),
        "58.00",
        "49.50",
        "Superstructure frame to 3rd floor. Rain days affected concrete pours.",
    ),
    (
        date(2026, 9, 15),
        "66.00",
        "55.50",
        "Roofing 60% complete; MEP first-fix started on lower floors.",
    ),
]


def _get_or_create_demo_user() -> User:
    user, created = User.objects.get_or_create(
        email=DEMO_USER_EMAIL,
        defaults={"first_name": "Demo", "last_name": "Owner"},
    )
    if created:
        user.set_password(DEMO_USER_PASSWORD)
        user.save(update_fields=["password"])
        print(f"Created user {user.email}")
    else:
        print(f"User {user.email} already exists")
    return user


def _get_or_create_demo_organization(owner: User) -> Organization:
    organization = Organization.objects.filter(name=ORGANIZATION_NAME).first()
    if organization is not None:
        print(f"Organization '{organization.name}' already exists")
        return organization

    organization = org_services.create_organization(
        creator=owner, name=ORGANIZATION_NAME
    )
    print(f"Created organization '{organization.name}' ({organization.slug})")
    return organization


def _ensure_membership(user: User, organization: Organization) -> None:
    _, created = OrganizationMembership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={"role": Role.ORGANIZATION_ADMIN},
    )
    if created:
        print(f"Added {user.email} to '{organization.name}' as {Role.ORGANIZATION_ADMIN}")


def _create_project(organization: Organization) -> Project:
    project = project_services.create_project(
        organization=organization,
        name="Luxury Residence — Lekki",
        project_code=PROJECT_CODE,
        description=(
            "Five-bedroom luxury residence with staff quarters, pool house "
            "and basement parking."
        ),
        location="Lekki, Lagos",
        client_name="Adeyemi Family Trust",
        contractor_name="Marbleworks Construction Ltd",
        project_type=ProjectType.ESTATE_DEVELOPMENT,
        contract_value=Decimal("500000000.00"),
        currency="NGN",
        planned_start_date=date(2026, 6, 1),
        planned_end_date=date(2027, 8, 31),
        actual_start_date=date(2026, 6, 8),
    )
    print(f"Created project {project.project_code} — {project.name}")
    return project


def _add_budget_items(project: Project) -> None:
    for (
        category,
        code,
        description,
        original,
        approved,
        committed,
        actual,
    ) in BUDGET_ITEMS:
        project_services.add_budget_item(
            project=project,
            category=category,
            code=code,
            description=description,
            original_amount=Decimal(original),
            approved_amount=Decimal(approved),
            committed_amount=Decimal(committed),
            actual_amount=Decimal(actual),
        )
    print(f"Added {len(BUDGET_ITEMS)} budget items")


def _add_progress_updates(project: Project, submitted_by: User) -> None:
    for reporting_date, planned, actual, notes in PROGRESS_UPDATES:
        project_services.add_progress_update(
            project=project,
            submitted_by=submitted_by,
            reporting_date=reporting_date,
            planned_progress_percent=Decimal(planned),
            actual_progress_percent=Decimal(actual),
            notes=notes,
        )
    print(f"Added {len(PROGRESS_UPDATES)} progress updates")


def _seed_payments(project: Project, submitter: User, reviewer: User) -> None:
    """
    One payment application per point in the review lifecycle, so the
    Payments page and dashboard have a realistic mix to render.
    """
    # 1. PA-0001: submitted, untouched — shows up as pending.
    project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("35000000.00"),
        submission_date=date(2026, 7, 15),
    )

    # 2. PA-0002: moved into review — also pending.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("42000000.00"),
        submission_date=date(2026, 8, 5),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )

    # 3. PA-0003: recommended for a lower amount than requested — pending.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("60000000.00"),
        submission_date=date(2026, 8, 20),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECOMMEND",
        amount=Decimal("54000000.00"),
        notes="Deducted unapproved variation on tiling spec.",
    )

    # 4. PA-0004: rejected — a duplicate of an already-paid claim.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("15000000.00"),
        submission_date=date(2026, 6, 25),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="REJECT",
        notes="Duplicate of items already covered under PA-0000 (pre-seed).",
    )

    # 5. PA-0005: taken all the way to a partial payment — approved
    #    28,000,000 recommended in full, but only 18,000,000 paid so far.
    payment = project_services.create_payment(
        project=project,
        submitted_by=submitter,
        amount_requested=Decimal("28000000.00"),
        submission_date=date(2026, 6, 10),
    )
    project_services.PaymentService.review(
        payment=payment, reviewer=reviewer, decision="START_REVIEW"
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECOMMEND",
        amount=Decimal("28000000.00"),
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="APPROVE",
        amount=Decimal("28000000.00"),
    )
    project_services.PaymentService.review(
        payment=payment,
        reviewer=reviewer,
        decision="RECORD_PAYMENT",
        amount=Decimal("18000000.00"),
    )

    print("Seeded 5 payment applications across the full review lifecycle")


def run() -> None:
    user = _get_or_create_demo_user()
    organization = _get_or_create_demo_organization(user)
    _ensure_membership(user, organization)

    if Project.objects.filter(
        organization=organization, project_code=PROJECT_CODE
    ).exists():
        print(
            f"Project '{PROJECT_CODE}' already exists in '{organization.name}' — "
            "nothing more to seed."
        )
        return

    project = _create_project(organization)
    _add_budget_items(project)
    _add_progress_updates(project, submitted_by=user)
    _seed_payments(project, submitter=user, reviewer=user)

    print()
    print("Demo data seeded.")
    print(f"  Login:        {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD}")
    print(f"  Organization: {organization.name} ({organization.id})")
    print(f"  Project:      {project.project_code} ({project.id})")


if __name__ == "__main__":
    run()