"""Read-side queries for inspections, inspection items, and evidence."""

from django.db.models import QuerySet

from apps.inspections.models import Inspection, InspectionItem, ProjectEvidence
from apps.projects.models import Project


def inspections_for_project(project: Project) -> QuerySet[Inspection]:
    return project.inspections.select_related("inspector").all()


def inspection_queryset_for_user(user) -> QuerySet[Inspection]:
    if not getattr(user, "is_authenticated", False):
        return Inspection.objects.none()
    return (
        Inspection.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "inspector")
        .distinct()
    )


def items_for_inspection(inspection: Inspection) -> QuerySet[InspectionItem]:
    return inspection.items.all()


def inspection_item_queryset_for_user(user) -> QuerySet[InspectionItem]:
    if not getattr(user, "is_authenticated", False):
        return InspectionItem.objects.none()
    return (
        InspectionItem.objects.filter(
            inspection__project__organization__memberships__user=user
        )
        .select_related("inspection", "inspection__project", "inspection__project__organization")
        .distinct()
    )


def evidence_for_project(project: Project, *, inspection_id=None) -> QuerySet[ProjectEvidence]:
    queryset = project.evidence_items.select_related("inspection", "uploaded_by").all()
    if inspection_id:
        queryset = queryset.filter(inspection_id=inspection_id)
    return queryset


def evidence_queryset_for_user(user) -> QuerySet[ProjectEvidence]:
    if not getattr(user, "is_authenticated", False):
        return ProjectEvidence.objects.none()
    return (
        ProjectEvidence.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "inspection", "uploaded_by")
        .distinct()
    )
