"""
Stage 2 financial/progress truth models.

Every model here traces back to a `Project`, and every `Project` belongs to
an `Organization` — there is no orphaned financial or progress record.
Money fields always use `DecimalField` (never float) and are validated
non-negative via `common.validators.MONEY_VALIDATORS`.
"""

from typing import ClassVar

from django.conf import settings
from django.db import models

from common.models import BaseModel
from common.validators import MONEY_VALIDATORS, PERCENT_VALIDATORS


class ProjectType(models.TextChoices):
    RESIDENTIAL = "RESIDENTIAL", "Residential"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    INDUSTRIAL = "INDUSTRIAL", "Industrial"
    HOSPITALITY = "HOSPITALITY", "Hospitality"
    ESTATE_DEVELOPMENT = "ESTATE_DEVELOPMENT", "Estate development"
    INFRASTRUCTURE = "INFRASTRUCTURE", "Infrastructure"
    RENOVATION = "RENOVATION", "Renovation"
    OTHER = "OTHER", "Other"


class ProjectStatus(models.TextChoices):
    PLANNING = "PLANNING", "Planning"
    ACTIVE = "ACTIVE", "Active"
    ON_HOLD = "ON_HOLD", "On hold"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


# Legal project status transitions. A status not present as a key has no
# further transitions (terminal). Enforced in apps.projects.services.
PROJECT_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    ProjectStatus.PLANNING: frozenset({ProjectStatus.ACTIVE, ProjectStatus.CANCELLED}),
    ProjectStatus.ACTIVE: frozenset(
        {ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}
    ),
    ProjectStatus.ON_HOLD: frozenset({ProjectStatus.ACTIVE, ProjectStatus.CANCELLED}),
}


class Project(BaseModel):
    # PROTECT: an organization must not silently take its projects (and
    # their financial history) down with it. There is no organization
    # delete endpoint today, but the constraint documents intent.
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="projects",
    )
    name = models.CharField(max_length=200)
    project_code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    contractor_name = models.CharField(max_length=200, blank=True)
    project_type = models.CharField(
        max_length=32, choices=ProjectType.choices, default=ProjectType.OTHER
    )
    contract_value = models.DecimalField(
        max_digits=18, decimal_places=2, validators=MONEY_VALIDATORS
    )
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=ProjectStatus.choices, default=ProjectStatus.PLANNING
    )
    currency = models.CharField(max_length=3, default="NGN")

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["organization", "project_code"],
                name="projects_project_org_code_unique",
            ),
        ]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self):
        return f"{self.project_code} — {self.name}"


class ProjectBudget(BaseModel):
    """
    One budget envelope per project. Totals are never stored — they're
    always computed from `BudgetItem` rows (via `apps.projects.selectors`)
    so a total can never drift out of sync with its line items.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="budget"
    )

    def __str__(self):
        return f"Budget for {self.project.project_code}"


class BudgetCategory(models.TextChoices):
    CIVIL = "CIVIL", "Civil"
    STRUCTURAL = "STRUCTURAL", "Structural"
    ARCHITECTURAL = "ARCHITECTURAL", "Architectural"
    MEP = "MEP", "MEP"
    FINISHES = "FINISHES", "Finishes"
    EXTERNAL_WORKS = "EXTERNAL_WORKS", "External works"
    PROFESSIONAL_FEES = "PROFESSIONAL_FEES", "Professional fees"
    PROCUREMENT = "PROCUREMENT", "Procurement"
    OTHER = "OTHER", "Other"


class BudgetItem(BaseModel):
    budget = models.ForeignKey(
        ProjectBudget, on_delete=models.CASCADE, related_name="items"
    )
    category = models.CharField(
        max_length=32, choices=BudgetCategory.choices, default=BudgetCategory.OTHER
    )
    code = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255)

    # Never collapsed into one field — each stage of the cost lifecycle is
    # tracked independently (see README "financial data model").
    original_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, default=0
    )
    approved_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, default=0
    )
    committed_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, default=0
    )
    actual_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, default=0
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["category", "created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["budget", "category"]),
        ]

    def __str__(self):
        return f"{self.category}: {self.description}"


class ProgressUpdate(BaseModel):
    """
    Immutable historical record. The API only ever lists and creates these
    — never updates or deletes — so the progress history of a project can
    always be trusted and replayed.
    """

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="progress_updates"
    )
    reporting_date = models.DateField()
    planned_progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, validators=PERCENT_VALIDATORS
    )
    actual_progress_percent = models.DecimalField(
        max_digits=5, decimal_places=2, validators=PERCENT_VALIDATORS
    )
    notes = models.TextField(blank=True)
    # PROTECT: a progress record's authorship is part of the audit trail —
    # deleting the submitting user must not silently orphan or delete it.
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="progress_updates",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-reporting_date", "-created_at"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["project", "reporting_date"],
                name="projects_progress_project_date_unique",
            ),
        ]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "-reporting_date"]),
        ]

    def __str__(self):
        return f"{self.project.project_code} progress @ {self.reporting_date}"


class PaymentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    RECOMMENDED = "RECOMMENDED", "Recommended"
    APPROVED = "APPROVED", "Approved"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Partially paid"
    PAID = "PAID", "Paid"
    REJECTED = "REJECTED", "Rejected"


# Legal payment status transitions, enforced by PaymentService.review().
# PAID and REJECTED are terminal (no key => no further transitions).
PAYMENT_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    PaymentStatus.SUBMITTED: frozenset(
        {PaymentStatus.UNDER_REVIEW, PaymentStatus.REJECTED}
    ),
    PaymentStatus.UNDER_REVIEW: frozenset(
        {PaymentStatus.RECOMMENDED, PaymentStatus.REJECTED}
    ),
    PaymentStatus.RECOMMENDED: frozenset(
        {PaymentStatus.APPROVED, PaymentStatus.REJECTED}
    ),
    PaymentStatus.APPROVED: frozenset(
        {PaymentStatus.PARTIALLY_PAID, PaymentStatus.PAID}
    ),
    PaymentStatus.PARTIALLY_PAID: frozenset({PaymentStatus.PAID}),
}


class PaymentApplication(BaseModel):
    """
    A contractor payment request moving through review.

    `amount_requested`, `amount_recommended`, `amount_approved`, and
    `amount_paid` are four independent fields, never collapsed into one —
    see README "why requested/recommended/approved/paid are separate".
    """

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="payment_applications"
    )
    application_number = models.CharField(max_length=30)

    amount_requested = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS
    )
    amount_recommended = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        null=True,
        blank=True,
    )
    amount_approved = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        validators=MONEY_VALIDATORS,
        null=True,
        blank=True,
    )
    amount_paid = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, default=0
    )

    status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.SUBMITTED
    )

    submission_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)

    # PROTECT: who submitted/reviewed a payment is part of its audit trail.
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_payments",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_payments",
        null=True,
        blank=True,
    )
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["project", "application_number"],
                name="projects_payment_project_number_unique",
            ),
        ]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self):
        return f"{self.application_number} ({self.status})"
