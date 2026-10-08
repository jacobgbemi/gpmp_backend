"""
Write-side business logic for inspections, inspection items, and evidence.

`complete_inspection` is the one and only place `overall_status` and
`status=COMPLETED` are ever set together — mirrors
`apps.variations.services.approve_variation` being the sole path to
`APPROVED`. Items become immutable the moment their inspection reaches
`COMPLETED` (`_ensure_items_editable`), so a finalized inspection's
record can always be trusted.
"""

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.inspections.models import (
    INSPECTION_STATUS_TRANSITIONS,
    Inspection,
    InspectionItem,
    InspectionItemStatus,
    InspectionOverallStatus,
    InspectionStatus,
    ProjectEvidence,
)
from common.file_validation import (
    DOCUMENT,
    IMAGE,
    VIDEO,
    safe_display_filename,
    validate_upload,
)

_EVIDENCE_KIND_MAP = {
    "PHOTO": (IMAGE,),
    "SCREENSHOT": (IMAGE,),
    "VIDEO": (VIDEO,),
    "DOCUMENT": (DOCUMENT,),
    "OTHER": (IMAGE, VIDEO, DOCUMENT),
}


def _full_clean_and_save(instance):
    try:
        instance.full_clean()
        instance.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return instance


# ---------------------------------------------------------------------------
# Inspections
# ---------------------------------------------------------------------------


@transaction.atomic
def create_inspection(*, project, inspector, **fields) -> Inspection:
    inspection = Inspection(project=project, inspector=inspector, **fields)
    return _full_clean_and_save(inspection)


@transaction.atomic
def update_inspection(*, inspection: Inspection, data: dict) -> Inspection:
    new_status = data.get("status")
    if new_status and new_status != inspection.status:
        if new_status == InspectionStatus.COMPLETED:
            raise ValidationError(
                {
                    "status": (
                        "Use POST /api/inspections/{id}/complete/ to complete an "
                        "inspection — it cannot be set directly."
                    )
                }
            )
        allowed = INSPECTION_STATUS_TRANSITIONS.get(inspection.status, frozenset())
        if new_status not in allowed:
            raise ValidationError(
                {
                    "status": (
                        f"Cannot transition inspection from '{inspection.status}' to "
                        f"'{new_status}'."
                    )
                }
            )

    for field, value in data.items():
        setattr(inspection, field, value)
    return _full_clean_and_save(inspection)


@transaction.atomic
def complete_inspection(*, inspection: Inspection) -> Inspection:
    if inspection.status == InspectionStatus.COMPLETED:
        raise ValidationError({"status": "This inspection has already been completed."})
    if inspection.status == InspectionStatus.CANCELLED:
        raise ValidationError({"status": "A cancelled inspection cannot be completed."})

    statuses = set(inspection.items.values_list("status", flat=True))
    if InspectionItemStatus.FAIL in statuses:
        overall = InspectionOverallStatus.FAIL
    elif InspectionItemStatus.OBSERVATION in statuses:
        overall = InspectionOverallStatus.OBSERVATION
    elif statuses:
        overall = InspectionOverallStatus.PASS_
    else:
        overall = InspectionOverallStatus.PENDING

    inspection.status = InspectionStatus.COMPLETED
    inspection.overall_status = overall
    inspection.completed_at = timezone.now()
    inspection.save()
    return inspection


def _ensure_items_editable(inspection: Inspection) -> None:
    if inspection.status == InspectionStatus.COMPLETED:
        raise ValidationError(
            {"detail": "This inspection is completed — its items are locked."}
        )


@transaction.atomic
def add_inspection_item(*, inspection: Inspection, **fields) -> InspectionItem:
    _ensure_items_editable(inspection)
    item = InspectionItem(inspection=inspection, **fields)
    return _full_clean_and_save(item)


@transaction.atomic
def update_inspection_item(*, item: InspectionItem, data: dict) -> InspectionItem:
    _ensure_items_editable(item.inspection)
    for field, value in data.items():
        setattr(item, field, value)
    return _full_clean_and_save(item)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@transaction.atomic
def create_evidence(
    *, project, uploaded_by, uploaded_file, evidence_type: str, inspection=None, **fields
) -> ProjectEvidence:
    if inspection is not None and inspection.project_id != project.id:
        raise ValidationError({"inspection": "This inspection does not belong to this project."})

    kinds = _EVIDENCE_KIND_MAP.get(evidence_type, (IMAGE, VIDEO, DOCUMENT))
    max_size = django_settings.MAX_EVIDENCE_UPLOAD_SIZE_MB * 1024 * 1024
    extension = validate_upload(uploaded_file, kinds=kinds, max_size_bytes=max_size)

    evidence = ProjectEvidence(
        project=project,
        inspection=inspection,
        uploaded_by=uploaded_by,
        evidence_type=evidence_type,
        original_filename=safe_display_filename(uploaded_file.name),
        file_extension=extension,
        content_type=uploaded_file.content_type or "",
        file_size=uploaded_file.size,
        **fields,
    )
    evidence.file = uploaded_file
    return _full_clean_and_save(evidence)
