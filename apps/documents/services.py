"""
Write-side business logic for document folders and documents.

`create_new_version` is the only path that ever creates a second+ row
sharing a `document_group` — it flips the previous latest version's
`is_latest` to False in the same transaction as creating the new row, so
"what's current" is never ambiguous even mid-request.
"""

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.documents.models import Document, DocumentFolder
from common.file_validation import (
    DOCUMENT,
    IMAGE,
    safe_display_filename,
    validate_upload,
)

_DOCUMENT_KIND_MAP = {
    "DRAWING": (DOCUMENT, IMAGE),
}
_DEFAULT_KINDS = (DOCUMENT,)


def _full_clean_and_save(instance):
    try:
        instance.full_clean()
        instance.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return instance


def _validate_folder(*, folder, project):
    if folder is not None and folder.project_id != project.id:
        raise ValidationError({"folder": "This folder does not belong to this project."})


@transaction.atomic
def create_folder(*, project, **fields) -> DocumentFolder:
    parent = fields.get("parent")
    if parent is not None and parent.project_id != project.id:
        raise ValidationError({"parent": "The parent folder does not belong to this project."})
    folder = DocumentFolder(project=project, **fields)
    try:
        return _full_clean_and_save(folder)
    except IntegrityError as exc:
        raise ValidationError(
            {"name": "A folder with this name already exists at this location."}
        ) from exc


@transaction.atomic
def create_document(
    *, project, uploaded_by, uploaded_file, document_type: str, folder=None, **fields
) -> Document:
    _validate_folder(folder=folder, project=project)

    kinds = _DOCUMENT_KIND_MAP.get(document_type, _DEFAULT_KINDS)
    max_size = django_settings.MAX_DOCUMENT_UPLOAD_SIZE_MB * 1024 * 1024
    extension = validate_upload(uploaded_file, kinds=kinds, max_size_bytes=max_size)

    document = Document(
        project=project,
        folder=folder,
        uploaded_by=uploaded_by,
        document_type=document_type,
        version=1,
        is_latest=True,
        original_filename=safe_display_filename(uploaded_file.name),
        file_extension=extension,
        content_type=uploaded_file.content_type or "",
        file_size=uploaded_file.size,
        **fields,
    )
    document.file = uploaded_file
    return _full_clean_and_save(document)


@transaction.atomic
def create_new_version(
    *, previous: Document, uploaded_by, uploaded_file, change_notes: str = ""
) -> Document:
    kinds = _DOCUMENT_KIND_MAP.get(previous.document_type, _DEFAULT_KINDS)
    max_size = django_settings.MAX_DOCUMENT_UPLOAD_SIZE_MB * 1024 * 1024
    extension = validate_upload(uploaded_file, kinds=kinds, max_size_bytes=max_size)

    new_version = Document(
        project=previous.project,
        folder=previous.folder,
        name=previous.name,
        description=previous.description,
        document_type=previous.document_type,
        status=previous.status,
        uploaded_by=uploaded_by,
        document_group=previous.document_group,
        version=previous.version + 1,
        is_latest=True,
        change_notes=change_notes,
        original_filename=safe_display_filename(uploaded_file.name),
        file_extension=extension,
        content_type=uploaded_file.content_type or "",
        file_size=uploaded_file.size,
    )
    new_version.file = uploaded_file

    try:
        new_version.full_clean()
        new_version.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    except IntegrityError as exc:
        raise ValidationError(
            {"version": "This version number already exists for this document."}
        ) from exc

    Document.objects.filter(document_group=previous.document_group).exclude(
        id=new_version.id
    ).update(is_latest=False)
    return new_version


@transaction.atomic
def update_document(*, document: Document, data: dict) -> Document:
    """Metadata-only update — never touches file/version/document_group."""
    folder = data.get("folder", document.folder)
    _validate_folder(folder=folder, project=document.project)

    for field, value in data.items():
        setattr(document, field, value)
    return _full_clean_and_save(document)
