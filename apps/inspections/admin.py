from typing import ClassVar

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.inspections.models import Inspection, InspectionItem, ProjectEvidence


class InspectionItemInline(TabularInline):
    model = InspectionItem
    extra = 0


@admin.register(Inspection)
class InspectionAdmin(ModelAdmin):
    list_display = (
        "project",
        "inspection_type",
        "inspection_date",
        "inspector",
        "status",
        "overall_status",
    )
    list_filter = ("status", "overall_status", "inspection_type", "project__organization")
    search_fields = ("project__project_code", "project__name", "location")
    autocomplete_fields: ClassVar[list[str]] = ["project", "inspector"]
    readonly_fields = ("id", "overall_status", "completed_at", "created_at", "updated_at")
    date_hierarchy = "inspection_date"
    inlines: ClassVar[list[type[admin.TabularInline]]] = [InspectionItemInline]


@admin.register(InspectionItem)
class InspectionItemAdmin(ModelAdmin):
    list_display = ("inspection", "category", "status", "severity")
    list_filter = ("status", "severity", "category")
    search_fields = ("description", "inspection__project__project_code")
    autocomplete_fields: ClassVar[list[str]] = ["inspection"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProjectEvidence)
class ProjectEvidenceAdmin(ModelAdmin):
    list_display = (
        "title",
        "project",
        "evidence_type",
        "original_filename",
        "file_size",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("evidence_type", "project__organization")
    search_fields = ("title", "original_filename", "project__project_code")
    autocomplete_fields: ClassVar[list[str]] = ["project", "inspection", "uploaded_by"]
    readonly_fields = (
        "id",
        "original_filename",
        "file_extension",
        "content_type",
        "file_size",
        "created_at",
        "updated_at",
    )
