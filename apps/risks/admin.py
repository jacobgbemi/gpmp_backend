from typing import ClassVar

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.risks.models import Issue, Risk


@admin.register(Risk)
class RiskAdmin(ModelAdmin):
    list_display = (
        "title",
        "project",
        "category",
        "probability",
        "impact",
        "risk_score",
        "status",
        "owner",
        "target_date",
    )
    list_filter = ("status", "category", "response", "project__organization")
    search_fields = ("title", "project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project", "owner"]
    readonly_fields = ("id", "risk_score", "created_at", "updated_at")
    date_hierarchy = "target_date"


@admin.register(Issue)
class IssueAdmin(ModelAdmin):
    list_display = (
        "title",
        "project",
        "severity",
        "status",
        "owner",
        "target_date",
    )
    list_filter = ("status", "severity", "project__organization")
    search_fields = ("title", "project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project", "owner"]
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "target_date"
