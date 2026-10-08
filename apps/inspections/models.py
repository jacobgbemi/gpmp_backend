"""
Stage 4 — Inspections, inspection items, and site evidence.

`Inspection.overall_status` is never client-set — it is always computed
from its items by `apps.inspections.services.complete_inspection`, the
same "server computes, client never sets" principle as `Risk.risk_score`
in Stage 3. Items become immutable once their inspection is `COMPLETED`,
mirroring `ProgressUpdate`'s immutability in Stage 2 but scoped to a
lifecycle stage rather than forever.
"""

from typing import ClassVar

from django.conf import settings
from django.db import models

from common.models import BaseModel


class InspectionType(models.TextChoices):
    ROUTINE = "ROUTINE", "Routine"
    PAYMENT_VERIFICATION = "PAYMENT_VERIFICATION", "Payment verification"
    PROGRESS_VERIFICATION = "PROGRESS_VERIFICATION", "Progress verification"
    QUALITY = "QUALITY", "Quality"
    MILESTONE = "MILESTONE", "Milestone"
    SPECIAL = "SPECIAL", "Special"


class InspectionStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


INSPECTION_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    InspectionStatus.SCHEDULED: frozenset(
        {InspectionStatus.IN_PROGRESS, InspectionStatus.CANCELLED}
    ),
    InspectionStatus.IN_PROGRESS: frozenset(
        {InspectionStatus.CANCELLED}
    ),  # COMPLETED only via the dedicated /complete/ action
}


class InspectionOverallStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PASS_ = "PASS", "Pass"
    OBSERVATION = "OBSERVATION", "Observation"
    FAIL = "FAIL", "Fail"


class Inspection(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="inspections"
    )
    inspection_type = models.CharField(
        max_length=32, choices=InspectionType.choices, default=InspectionType.ROUTINE
    )
    inspection_date = models.DateField()
    # PROTECT: the inspector of record is part of the assurance trail.
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inspections"
    )
    location = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=16, choices=InspectionStatus.choices, default=InspectionStatus.SCHEDULED
    )
    # Never client-writable — computed by services.complete_inspection().
    overall_status = models.CharField(
        max_length=16,
        choices=InspectionOverallStatus.choices,
        default=InspectionOverallStatus.PENDING,
        editable=False,
    )
    recommendations = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-inspection_date", "-created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "inspection_type"]),
        ]

    def __str__(self):
        return f"{self.get_inspection_type_display()} inspection @ {self.inspection_date}"


class InspectionItemCategory(models.TextChoices):
    PROGRESS = "PROGRESS", "Progress"
    QUALITY = "QUALITY", "Quality"
    MATERIALS = "MATERIALS", "Materials"
    CONTRACTOR = "CONTRACTOR", "Contractor"
    SAFETY = "SAFETY", "Safety"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    DOCUMENTATION = "DOCUMENTATION", "Documentation"
    OTHER = "OTHER", "Other"


class InspectionItemStatus(models.TextChoices):
    PASS_ = "PASS", "Pass"
    FAIL = "FAIL", "Fail"
    OBSERVATION = "OBSERVATION", "Observation"
    NOT_APPLICABLE = "NOT_APPLICABLE", "Not applicable"


class InspectionItemSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class InspectionItem(BaseModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="items")
    category = models.CharField(
        max_length=32,
        choices=InspectionItemCategory.choices,
        default=InspectionItemCategory.OTHER,
    )
    description = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=InspectionItemStatus.choices,
        default=InspectionItemStatus.OBSERVATION,
    )
    severity = models.CharField(
        max_length=16,
        choices=InspectionItemSeverity.choices,
        default=InspectionItemSeverity.LOW,
    )
    recommendation = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["inspection", "status"]),
        ]

    def __str__(self):
        return f"{self.category}: {self.description[:40]}"


class EvidenceType(models.TextChoices):
    PHOTO = "PHOTO", "Photo"
    VIDEO = "VIDEO", "Video"
    DOCUMENT = "DOCUMENT", "Document"
    SCREENSHOT = "SCREENSHOT", "Screenshot"
    OTHER = "OTHER", "Other"


def _evidence_upload_path(instance: "ProjectEvidence", filename: str) -> str:
    # `filename` (client-supplied) is intentionally ignored — see
    # common.file_validation.safe_upload_path. instance.file_extension is
    # set by the service *before* .save() from the already-validated
    # extension, never from this callback's `filename` argument.
    from common.file_validation import safe_upload_path

    return safe_upload_path(
        prefix="evidence", project_id=instance.project_id, extension=instance.file_extension
    )


class ProjectEvidence(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="evidence_items"
    )
    # Optional: evidence can support a specific inspection, or stand alone
    # (general progress/milestone evidence with no inspection attached).
    inspection = models.ForeignKey(
        Inspection, on_delete=models.CASCADE, related_name="evidence_items", null=True, blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(
        max_length=16, choices=EvidenceType.choices, default=EvidenceType.OTHER
    )

    file = models.FileField(upload_to=_evidence_upload_path)
    original_filename = models.CharField(max_length=200)
    file_extension = models.CharField(max_length=10)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()

    captured_at = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # PROTECT: the uploader's identity is part of the evidence's chain of
    # custody — deleting the user must not silently orphan or delete it.
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_evidence"
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "evidence_type"]),
            models.Index(fields=["inspection"]),
        ]

    def __str__(self):
        return f"{self.evidence_type}: {self.title}"
