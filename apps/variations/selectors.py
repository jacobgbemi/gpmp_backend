"""Read-side queries for variations."""

from django.db.models import QuerySet

from apps.projects.models import Project
from apps.variations.models import Variation


def variations_for_project(project: Project) -> QuerySet[Variation]:
    return project.variations.select_related("created_by", "approved_by").all()


def variation_queryset_for_user(user) -> QuerySet[Variation]:
    """Variations scoped through the project's organization membership."""
    if not getattr(user, "is_authenticated", False):
        return Variation.objects.none()
    return (
        Variation.objects.filter(project__organization__memberships__user=user)
        .select_related("project", "project__organization", "created_by", "approved_by")
        .distinct()
    )


def next_variation_number(project: Project) -> str:
    count = Variation.objects.filter(project=project).count()
    return f"VAR-{count + 1:04d}"
