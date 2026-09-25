from typing import ClassVar

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.variations.models import Variation


@admin.register(Variation)
class VariationAdmin(ModelAdmin):
    list_display = (
        "variation_number",
        "title",
        "project",
        "category",
        "status",
        "requested_amount",
        "estimated_amount",
        "approved_amount",
    )
    list_filter = ("status", "category", "project__organization")
    search_fields = (
        "variation_number",
        "title",
        "project__project_code",
        "project__name",
    )
    autocomplete_fields: ClassVar[list[str]] = ["project", "created_by", "approved_by"]
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "requested_date"
