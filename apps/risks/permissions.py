"""
Risk/Issue permission logic — reuses the same project-role resolution as
`apps.projects.permissions`.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.projects.permissions import PROJECT_WRITE_ROLES, get_project_role


class IsRiskWriterOrReadOnly(BasePermission):
    """Members may read; only PROJECT_WRITE_ROLES may create/modify a risk."""

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in PROJECT_WRITE_ROLES


class IsIssueWriterOrReadOnly(BasePermission):
    """Members may read; only PROJECT_WRITE_ROLES may create/modify an issue."""

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in PROJECT_WRITE_ROLES
