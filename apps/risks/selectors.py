"""Read-side queries for risks and issues."""

from django.db.models import QuerySet

from apps.projects.models import Project
from apps.risks.models import Issue, Risk


def risks_for_project(project: Project) -> QuerySet[Risk]:
    return project.risks.select_related("owner").all()


def risk_queryset_for_user(user) -> QuerySet[Risk]:
    if not getattr(user, "is_authenticated", False):
        return Risk.objects.none()
    return (
        Risk.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "owner")
        .distinct()
    )


def issues_for_project(project: Project) -> QuerySet[Issue]:
    return project.issues.select_related("owner").all()


def issue_queryset_for_user(user) -> QuerySet[Issue]:
    if not getattr(user, "is_authenticated", False):
        return Issue.objects.none()
    return (
        Issue.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "owner")
        .distinct()
    )
