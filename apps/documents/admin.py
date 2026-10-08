from typing import ClassVar

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.documents.models import Document, DocumentFolder


@admin.register(DocumentFolder)
class DocumentFolderAdmin(ModelAdmin):
    list_display = ("name", "project", "parent")
    list_filter = ("project__organization",)
    search_fields = ("name", "project__project_code", "project__name")
    autocomplete_fields: ClassVar[list[str]] = ["project", "parent"]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = (
        "name",
        "project",
        "document_type",
        "version",
        "is_latest",
        "status",
        "file_size",
        "uploaded_by",
    )
    list_filter = ("document_type", "status", "is_latest", "project__organization")
    search_fields = ("name", "original_filename", "project__project_code")
    autocomplete_fields: ClassVar[list[str]] = ["project", "folder", "uploaded_by"]
    readonly_fields = (
        "id",
        "document_group",
        "version",
        "is_latest",
        "original_filename",
        "file_extension",
        "content_type",
        "file_size",
        "created_at",
        "updated_at",
    )
