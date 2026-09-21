from typing import ClassVar

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.projects.models import (
    BudgetItem,
    PaymentApplication,
    ProgressUpdate,
    Project,
    ProjectBudget,
)


class BudgetItemInline(TabularInline):
    model = BudgetItem
    extra = 0


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = (
        "project_code",
        "name",
        "organization",
        "status",
        "project_type",
        "contract_value",
        "currency",
        "created_at",
    )
    list_filter = ("status", "project_type", "organization")
    search_fields = ("project_code", "name", "organization__name", "client_name")
    autocomplete_fields: ClassVar[list[str]] = ["organization"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(ModelAdmin):
    list_display = ("project", "created_at")
    search_fields = ("project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project"]
    readonly_fields = ("id", "created_at", "updated_at")
    inlines: ClassVar[list[type[admin.TabularInline]]] = [BudgetItemInline]


@admin.register(BudgetItem)
class BudgetItemAdmin(ModelAdmin):
    list_display = (
        "budget",
        "category",
        "description",
        "original_amount",
        "approved_amount",
        "committed_amount",
        "actual_amount",
    )
    list_filter = ("category",)
    search_fields = ("description", "code", "budget__project__project_code")
    autocomplete_fields: ClassVar[list[str]] = ["budget"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(ModelAdmin):
    list_display = (
        "project",
        "reporting_date",
        "planned_progress_percent",
        "actual_progress_percent",
        "submitted_by",
    )
    list_filter = ("project__organization",)
    search_fields = ("project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project", "submitted_by"]
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "reporting_date"


@admin.register(PaymentApplication)
class PaymentApplicationAdmin(ModelAdmin):
    list_display = (
        "application_number",
        "project",
        "status",
        "amount_requested",
        "amount_recommended",
        "amount_approved",
        "amount_paid",
    )
    list_filter = ("status", "project__organization")
    search_fields = ("application_number", "project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project", "submitted_by", "reviewer"]
    readonly_fields = ("id", "created_at", "updated_at")
