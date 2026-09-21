"""
Write-side business logic for projects, budgets, progress, and payments.

`PaymentService.review()` is the payment lifecycle state machine — the
single place that decides which status transitions are legal and what each
transition requires. Views never mutate `PaymentApplication.status`
directly.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.projects.models import (
    PAYMENT_STATUS_TRANSITIONS,
    PROJECT_STATUS_TRANSITIONS,
    BudgetItem,
    PaymentApplication,
    PaymentStatus,
    ProgressUpdate,
    Project,
    ProjectBudget,
)
from apps.projects.selectors import next_application_number

# Payment statuses a project may not be deleted while it has: real money has
# moved (or is committed to moving) and the record must be preserved.
_PAYMENT_STATUSES_BLOCKING_DELETE = frozenset(
    {PaymentStatus.APPROVED, PaymentStatus.PARTIALLY_PAID, PaymentStatus.PAID}
)


def _validate_project_dates(
    *, planned_start_date, planned_end_date, actual_start_date, actual_end_date
):
    if (
        planned_start_date
        and planned_end_date
        and planned_end_date < planned_start_date
    ):
        raise ValidationError(
            {
                "planned_end_date": "Planned end date cannot be before the planned start date."
            }
        )
    if actual_start_date and actual_end_date and actual_end_date < actual_start_date:
        raise ValidationError(
            {
                "actual_end_date": "Actual end date cannot be before the actual start date."
            }
        )


@transaction.atomic
def create_project(*, organization, **fields) -> Project:
    _validate_project_dates(
        planned_start_date=fields.get("planned_start_date"),
        planned_end_date=fields.get("planned_end_date"),
        actual_start_date=fields.get("actual_start_date"),
        actual_end_date=fields.get("actual_end_date"),
    )
    try:
        project = Project.objects.create(organization=organization, **fields)
    except IntegrityError as exc:
        raise ValidationError(
            {
                "project_code": "A project with this code already exists in this organization."
            }
        ) from exc
    ProjectBudget.objects.create(project=project)
    return project


@transaction.atomic
def update_project(*, project: Project, data: dict) -> Project:
    new_status = data.get("status")
    if new_status and new_status != project.status:
        allowed = PROJECT_STATUS_TRANSITIONS.get(project.status, frozenset())
        if new_status not in allowed:
            raise ValidationError(
                {
                    "status": (
                        f"Cannot transition project from '{project.status}' to "
                        f"'{new_status}'."
                    )
                }
            )

    for field, value in data.items():
        setattr(project, field, value)

    _validate_project_dates(
        planned_start_date=project.planned_start_date,
        planned_end_date=project.planned_end_date,
        actual_start_date=project.actual_start_date,
        actual_end_date=project.actual_end_date,
    )

    try:
        project.full_clean()
        project.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict
            if hasattr(exc, "message_dict")
            else {"detail": exc.messages}
        ) from exc
    except IntegrityError as exc:
        raise ValidationError(
            {
                "project_code": "A project with this code already exists in this organization."
            }
        ) from exc
    return project


def delete_project(*, project: Project) -> None:
    has_settled_payments = project.payment_applications.filter(
        status__in=_PAYMENT_STATUSES_BLOCKING_DELETE
    ).exists()
    if has_settled_payments:
        raise ValidationError(
            {
                "detail": (
                    "This project has approved, partially paid, or paid payment "
                    "applications and cannot be deleted."
                )
            }
        )
    project.delete()


@transaction.atomic
def add_budget_item(*, project: Project, **fields) -> BudgetItem:
    budget, _ = ProjectBudget.objects.get_or_create(project=project)
    return BudgetItem.objects.create(budget=budget, **fields)


@transaction.atomic
def add_progress_update(*, project: Project, submitted_by, **fields) -> ProgressUpdate:
    try:
        return ProgressUpdate.objects.create(
            project=project, submitted_by=submitted_by, **fields
        )
    except IntegrityError as exc:
        raise ValidationError(
            {
                "reporting_date": (
                    "A progress update for this project and reporting date "
                    "already exists."
                )
            }
        ) from exc


@transaction.atomic
def create_payment(
    *,
    project: Project,
    submitted_by,
    amount_requested: Decimal,
    submission_date: date | None = None,
) -> PaymentApplication:
    return PaymentApplication.objects.create(
        project=project,
        submitted_by=submitted_by,
        amount_requested=amount_requested,
        submission_date=submission_date or timezone.now().date(),
        application_number=next_application_number(project),
        status=PaymentStatus.SUBMITTED,
    )


class PaymentReviewDecision:
    START_REVIEW = "START_REVIEW"
    RECOMMEND = "RECOMMEND"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RECORD_PAYMENT = "RECORD_PAYMENT"

    ALL = frozenset({START_REVIEW, RECOMMEND, APPROVE, REJECT, RECORD_PAYMENT})


class PaymentService:
    """Payment review state machine. See README "payment lifecycle"."""

    @staticmethod
    @transaction.atomic
    def review(
        *,
        payment: PaymentApplication,
        reviewer,
        decision: str,
        amount: Decimal | None = None,
        notes: str = "",
    ) -> PaymentApplication:
        if decision not in PaymentReviewDecision.ALL:
            raise ValidationError({"decision": f"Unknown decision '{decision}'."})

        handler = {
            PaymentReviewDecision.START_REVIEW: PaymentService._start_review,
            PaymentReviewDecision.RECOMMEND: PaymentService._recommend,
            PaymentReviewDecision.APPROVE: PaymentService._approve,
            PaymentReviewDecision.REJECT: PaymentService._reject,
            PaymentReviewDecision.RECORD_PAYMENT: PaymentService._record_payment,
        }[decision]

        handler(payment=payment, amount=amount, notes=notes)

        payment.reviewer = reviewer
        payment.review_date = timezone.now().date()
        if notes:
            payment.reviewer_notes = notes
        payment.save()
        return payment

    @staticmethod
    def _check_transition(payment: PaymentApplication, target_status: str) -> None:
        allowed = PAYMENT_STATUS_TRANSITIONS.get(payment.status, frozenset())
        if target_status not in allowed:
            raise ValidationError(
                {
                    "decision": (
                        f"Cannot move payment from '{payment.status}' to "
                        f"'{target_status}'."
                    )
                }
            )

    @staticmethod
    def _start_review(*, payment: PaymentApplication, amount, notes) -> None:
        PaymentService._check_transition(payment, PaymentStatus.UNDER_REVIEW)
        payment.status = PaymentStatus.UNDER_REVIEW

    @staticmethod
    def _recommend(*, payment: PaymentApplication, amount, notes) -> None:
        PaymentService._check_transition(payment, PaymentStatus.RECOMMENDED)
        if amount is None:
            raise ValidationError(
                {"amount": "amount_recommended is required to recommend a payment."}
            )
        if amount < 0:
            raise ValidationError({"amount": "Amount cannot be negative."})
        if amount > payment.amount_requested:
            raise ValidationError(
                {"amount": "Recommended amount cannot exceed the amount requested."}
            )
        payment.amount_recommended = amount
        payment.status = PaymentStatus.RECOMMENDED

    @staticmethod
    def _approve(*, payment: PaymentApplication, amount, notes) -> None:
        PaymentService._check_transition(payment, PaymentStatus.APPROVED)
        if amount is None:
            raise ValidationError(
                {"amount": "amount_approved is required to approve a payment."}
            )
        if amount < 0:
            raise ValidationError({"amount": "Amount cannot be negative."})
        if amount > payment.amount_recommended:
            raise ValidationError(
                {"amount": "Approved amount cannot exceed the recommended amount."}
            )
        payment.amount_approved = amount
        payment.status = PaymentStatus.APPROVED

    @staticmethod
    def _reject(*, payment: PaymentApplication, amount, notes) -> None:
        PaymentService._check_transition(payment, PaymentStatus.REJECTED)
        if not notes:
            raise ValidationError(
                {"notes": "A reason is required to reject a payment."}
            )
        payment.status = PaymentStatus.REJECTED

    @staticmethod
    def _record_payment(*, payment: PaymentApplication, amount, notes) -> None:
        if payment.status not in (PaymentStatus.APPROVED, PaymentStatus.PARTIALLY_PAID):
            raise ValidationError(
                {
                    "decision": f"Cannot record a payment while status is '{payment.status}'."
                }
            )
        if amount is None or amount <= 0:
            raise ValidationError({"amount": "A positive payment amount is required."})
        new_total = payment.amount_paid + amount
        if new_total > payment.amount_approved:
            raise ValidationError(
                {"amount": "Total paid cannot exceed the approved amount."}
            )
        payment.amount_paid = new_total
        payment.payment_date = timezone.now().date()
        payment.status = (
            PaymentStatus.PAID
            if new_total == payment.amount_approved
            else PaymentStatus.PARTIALLY_PAID
        )
