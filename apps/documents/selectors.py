"""Read-side queries for document folders and documents."""

from django.db.models import QuerySet

from apps.documents.models import Document, DocumentFolder
from apps.projects.models import Project


def folders_for_project(project: Project) -> QuerySet[DocumentFolder]:
    return project.document_folders.all()


def folder_queryset_for_user(user) -> QuerySet[DocumentFolder]:
    if not getattr(user, "is_authenticated", False):
        return DocumentFolder.objects.none()
    return (
        DocumentFolder.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization")
        .distinct()
    )


def documents_for_project(project: Project, *, folder_id=None, latest_only=True) -> QuerySet[Document]:
    queryset = project.documents.select_related("folder", "uploaded_by").all()
    if latest_only:
        queryset = queryset.filter(is_latest=True)
    if folder_id:
        queryset = queryset.filter(folder_id=folder_id)
    return queryset


def document_queryset_for_user(user) -> QuerySet[Document]:
    if not getattr(user, "is_authenticated", False):
        return Document.objects.none()
    return (
        Document.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "folder", "uploaded_by")
        .distinct()
    )


def versions_of(document: Document) -> QuerySet[Document]:
    return Document.objects.filter(document_group=document.document_group).order_by("-version")
