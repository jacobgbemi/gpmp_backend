from typing import ClassVar

from rest_framework import serializers

from apps.organizations.selectors import organizations_for_user
from apps.projects.models import (
    BudgetItem,
    PaymentApplication,
    ProgressUpdate,
    Project,
)
from apps.projects.services import PaymentReviewDecision


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields: ClassVar[list[str]] = [
            "id",
            "organization",
            "name",
            "project_code",
            "description",
            "location",
            "client_name",
            "contractor_name",
            "project_type",
            "contract_value",
            "planned_start_date",
            "planned_end_date",
            "actual_start_date",
            "actual_end_date",
            "status",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and "organization" in self.fields:
            # Restrict the choices to organizations the requester belongs
            # to — an org they aren't a member of is simply not a valid
            # choice, not a 403/404 leak.
            self.fields["organization"].queryset = organizations_for_user(request.user)
        if self.instance is None:
            # Creating: status always starts at PLANNING (see
            # services.create_project) — never client-settable, to block
            # mass assignment of an arbitrary initial status.
            self.fields["status"].read_only = True
        else:
            # Organization is immutable after creation.
            self.fields["organization"].read_only = True


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        fields: ClassVar[list[str]] = [
            "id",
            "category",
            "code",
            "description",
            "original_amount",
            "approved_amount",
            "committed_amount",
            "actual_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]


class ProjectBudgetSerializer(serializers.Serializer):
    """Read shape for GET /api/projects/{id}/budget/: items + computed totals."""

    items = BudgetItemSerializer(many=True, read_only=True)
    original_total = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    approved_total = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    committed_total = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    actual_total = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )


class ProgressUpdateSerializer(serializers.ModelSerializer):
    submitted_by_email = serializers.EmailField(
        source="submitted_by.email", read_only=True
    )
    progress_variance_percent = serializers.SerializerMethodField()

    class Meta:
        model = ProgressUpdate
        fields: ClassVar[list[str]] = [
            "id",
            "reporting_date",
            "planned_progress_percent",
            "actual_progress_percent",
            "progress_variance_percent",
            "notes",
            "submitted_by_email",
            "created_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "submitted_by_email",
            "progress_variance_percent",
            "created_at",
        ]

    def get_progress_variance_percent(self, obj):
        return obj.actual_progress_percent - obj.planned_progress_percent


class PaymentApplicationSerializer(serializers.ModelSerializer):
    submitted_by_email = serializers.EmailField(
        source="submitted_by.email", read_only=True
    )
    reviewer_email = serializers.EmailField(
        source="reviewer.email", read_only=True, default=None
    )
    submission_date = serializers.DateField(required=False)

    class Meta:
        model = PaymentApplication
        fields: ClassVar[list[str]] = [
            "id",
            "application_number",
            "amount_requested",
            "amount_recommended",
            "amount_approved",
            "amount_paid",
            "status",
            "submission_date",
            "review_date",
            "payment_date",
            "reviewer_notes",
            "submitted_by_email",
            "reviewer_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "application_number",
            "amount_recommended",
            "amount_approved",
            "amount_paid",
            "status",
            "review_date",
            "payment_date",
            "reviewer_notes",
            "submitted_by_email",
            "reviewer_email",
            "created_at",
            "updated_at",
        ]


class PaymentReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=sorted(PaymentReviewDecision.ALL))
    amount = serializers.DecimalField(
        max_digits=16, decimal_places=2, required=False, allow_null=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class DashboardSerializer(serializers.Serializer):
    original_budget = serializers.DecimalField(max_digits=18, decimal_places=2)
    approved_budget = serializers.DecimalField(max_digits=18, decimal_places=2)
    actual_spend = serializers.DecimalField(max_digits=18, decimal_places=2)
    committed_cost = serializers.DecimalField(max_digits=18, decimal_places=2)
    forecast_final_cost = serializers.DecimalField(max_digits=18, decimal_places=2)
    cost_variance = serializers.DecimalField(max_digits=18, decimal_places=2)
    planned_progress_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    actual_progress_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    schedule_variance = serializers.DecimalField(max_digits=5, decimal_places=2)
    pending_payments_count = serializers.IntegerField()
    pending_payments_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    as_of_reporting_date = serializers.DateField(allow_null=True)
