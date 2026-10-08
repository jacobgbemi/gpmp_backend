"""
Stage 4 — Document folders and documents, with basic versioning.

Versioning design (see README "document versioning"): all versions of one
document share a `document_group` UUID (generated fresh for version 1,
copied forward for every later version) plus a `version` integer. There is
no self-referential FK chain to walk — `Document.objects.filter(document_group=X)`
returns every version directly. `is_latest` is a denormalized flag flipped
by `apps.documents.services.create_new_version` so "what's current" is a
single indexed lookup rather than a MAX(version) query on every read.
"""

import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models

from common.models import BaseModel


class DocumentFolder(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="document_folders"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="subfolders", null=True, blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            # Postgres treats NULL as distinct from NULL, so a plain
            # UniqueConstraint on (project, parent, name) never catches two
            # root-level folders (parent IS NULL) with the same name — the
            # second constraint below closes that gap explicitly.
            models.UniqueConstraint(
                fields=["project", "parent", "name"],
                name="documents_folder_project_parent_name_unique",
            ),
            models.UniqueConstraint(
                fields=["project", "name"],
                condition=models.Q(parent__isnull=True),
                name="documents_folder_project_root_name_unique",
            ),
        ]

    def __str__(self):
        return self.name


class DocumentType(models.TextChoices):
    CONTRACT = "CONTRACT", "Contract"
    BOQ = "BOQ", "Bill of quantities"
    DRAWING = "DRAWING", "Drawing"
    SCHEDULE = "SCHEDULE", "Schedule"
    PAYMENT_DOCUMENT = "PAYMENT_DOCUMENT", "Payment document"
    REPORT = "REPORT", "Report"
    CORRESPONDENCE = "CORRESPONDENCE", "Correspondence"
    INSPECTION_EVIDENCE = "INSPECTION_EVIDENCE", "Inspection evidence"
    OTHER = "OTHER", "Other"


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


def _document_upload_path(instance: "Document", filename: str) -> str:
    # `filename` (client-supplied) is intentionally ignored — see
    # common.file_validation.safe_upload_path.
    from common.file_validation import safe_upload_path

    return safe_upload_path(
        prefix=f"documents/{instance.document_group}",
        project_id=instance.project_id,
        extension=instance.file_extension,
    )


class Document(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="documents"
    )
    folder = models.ForeignKey(
        DocumentFolder,
        on_delete=models.SET_NULL,
        related_name="documents",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    document_type = models.CharField(
        max_length=32, choices=DocumentType.choices, default=DocumentType.OTHER
    )
    status = models.CharField(
        max_length=16, choices=DocumentStatus.choices, default=DocumentStatus.ACTIVE
    )

    file = models.FileField(upload_to=_document_upload_path)
    original_filename = models.CharField(max_length=200)
    file_extension = models.CharField(max_length=10)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()

    # Versioning — see module docstring.
    document_group = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.PositiveIntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    change_notes = models.TextField(blank=True)

    # PROTECT: who uploaded a given version is part of the document's
    # audit trail.
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents"
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-is_latest", "-version"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["document_group", "version"],
                name="documents_document_group_version_unique",
            ),
        ]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "document_type"]),
            models.Index(fields=["document_group", "is_latest"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"
