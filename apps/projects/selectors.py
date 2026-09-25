"""
Read-side queries.

Every query in this module starts from `projects_for_user`, so a project
(or anything nested under it) belonging to an organization the requester
isn't a member of is simply absent from the result — never a permission
error, just nothing there. This is what makes cross-organization access
return 404 instead of 403 (see README "organization isolation strategy").
"""

from decimal import Decimal

from django.db.models import DecimalField, QuerySet, Sum
from django.db.models.functions import Coalesce

from apps.projects.models import (
    PaymentApplication,
    PaymentStatus,
    Project,
    ProjectBudget,
)
from apps.variations.models import (
    VARIATION_APPROVED_STATUSES,
    VARIATION_PENDING_STATUSES,
    Variation,
)

ZERO = Decimal("0.00")
_MONEY = DecimalField(max_digits=18, decimal_places=2)

# Payment statuses that represent money not yet finalized (approved/paid).
PENDING_PAYMENT_STATUSES = frozenset(
    {
        PaymentStatus.SUBMITTED,
        PaymentStatus.UNDER_REVIEW,
        PaymentStatus.RECOMMENDED,
    }
)


def projects_for_user(user) -> QuerySet[Project]:
    """
    Projects belonging to any organization the user is a member of.

    The ONLY queryset the projects API uses — this is the isolation
    boundary. A project in an organization the user doesn't belong to is
    simply not in this queryset.
    """
    if not getattr(user, "is_authenticated", False):
        return Project.objects.none()
    return (
        Project.objects.filter(organization__memberships__user=user)
        .select_related("organization")
        .distinct()
    )


def budget_items_for_project(project: Project):
    budget = ProjectBudget.objects.filter(project=project).first()
    if budget is None:
        return None, []
    return budget, list(budget.items.all())


def progress_updates_for_project(project: Project):
    return project.progress_updates.select_related("submitted_by").all()


def latest_progress_update(project: Project):
    return project.progress_updates.order_by("-reporting_date", "-created_at").first()


def payments_for_project(project: Project):
    return project.payment_applications.select_related("submitted_by", "reviewer").all()


def payment_queryset_for_user(user) -> QuerySet[PaymentApplication]:
    """Payments scoped through the same organization-membership boundary."""
    if not getattr(user, "is_authenticated", False):
        return PaymentApplication.objects.none()
    return (
        PaymentApplication.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "submitted_by", "reviewer")
        .distinct()
    )


def _budget_totals(project: Project) -> dict[str, Decimal]:
    totals = ProjectBudget.objects.filter(project=project).aggregate(
        original_total=Coalesce(
            Sum("items__original_amount"), ZERO, output_field=_MONEY
        ),
        approved_total=Coalesce(
            Sum("items__approved_amount"), ZERO, output_field=_MONEY
        ),
        committed_total=Coalesce(
            Sum("items__committed_amount"), ZERO, output_field=_MONEY
        ),
        actual_total=Coalesce(Sum("items__actual_amount"), ZERO, output_field=_MONEY),
    )
    return {key: value or ZERO for key, value in totals.items()}


def _variation_totals(project: Project) -> dict[str, Decimal]:
    """
    See README "approved variation rule": only APPROVED/IMPLEMENTED/CLOSED
    variations count as real, approved financial impact.
    PROPOSED/UNDER_REVIEW variations are surfaced separately as *exposure*
    — money the project might cost, never money it already does.
    """
    variations = Variation.objects.filter(project=project)
    approved_total = variations.filter(status__in=VARIATION_APPROVED_STATUSES).aggregate(
        total=Coalesce(Sum("approved_amount"), ZERO, output_field=_MONEY)
    )["total"]
    pending_total = variations.filter(status__in=VARIATION_PENDING_STATUSES).aggregate(
        total=Coalesce(Sum("estimated_amount"), ZERO, output_field=_MONEY)
    )["total"]
    return {"approved_variations_total": approved_total, "pending_variations_exposure": pending_total}


def project_dashboard(project: Project) -> dict:
    """
    Compute the owner-facing dashboard for a project.

    Calculation rules (see README "dashboard calculation rules" for the
    full rationale):
      - forecast_final_cost      = actual_spend + committed_cost
      - cost_variance            = approved_budget - forecast_final_cost
                                    (positive => under budget, negative => over)
      - schedule_variance        = actual_progress - planned_progress
                                    (positive => ahead, negative => behind)
      - pending_payments         = payments not yet approved, rejected, or paid
      - approved_variations_total = Σ approved_amount of APPROVED/IMPLEMENTED/
                                     CLOSED variations only (see README
                                     "approved variation rule")
      - pending_variations_exposure = Σ estimated_amount of PROPOSED/
                                       UNDER_REVIEW variations — potential,
                                       not-yet-approved cost exposure
      - revised_approved_budget  = approved_budget + approved_variations_total
    """
    totals = _budget_totals(project)
    original_budget = totals["original_total"]
    approved_budget = totals["approved_total"]
    actual_spend = totals["actual_total"]
    committed_cost = totals["committed_total"]
    forecast_final_cost = actual_spend + committed_cost
    cost_variance = approved_budget - forecast_final_cost

    variation_totals = _variation_totals(project)
    revised_approved_budget = approved_budget + variation_totals["approved_variations_total"]

    latest = latest_progress_update(project)
    planned_progress = latest.planned_progress_percent if latest else ZERO
    actual_progress = latest.actual_progress_percent if latest else ZERO
    schedule_variance = actual_progress - planned_progress

    pending = payments_for_project(project).filter(status__in=PENDING_PAYMENT_STATUSES)
    pending_total = pending.aggregate(
        total=Coalesce(Sum("amount_requested"), ZERO, output_field=_MONEY)
    )["total"]

    return {
        "original_budget": original_budget,
        "approved_budget": approved_budget,
        "actual_spend": actual_spend,
        "committed_cost": committed_cost,
        "forecast_final_cost": forecast_final_cost,
        "cost_variance": cost_variance,
        "approved_variations_total": variation_totals["approved_variations_total"],
        "pending_variations_exposure": variation_totals["pending_variations_exposure"],
        "revised_approved_budget": revised_approved_budget,
        "planned_progress_percent": planned_progress,
        "actual_progress_percent": actual_progress,
        "schedule_variance": schedule_variance,
        "pending_payments_count": pending.count(),
        "pending_payments_total": pending_total,
        "as_of_reporting_date": latest.reporting_date if latest else None,
    }


# Used by services.create_payment to generate the next application number.
def next_application_number(project: Project) -> str:
    count = PaymentApplication.objects.filter(project=project).count()
    return f"PA-{count + 1:04d}"
