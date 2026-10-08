"""
Document/Folder permission logic — reuses PROJECT_WRITE_ROLES directly
(unlike inspections, document management stays with
PM/controls/admin — SITE_INSPECTOR is not extended write access here).
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.projects.permissions import PROJECT_WRITE_ROLES, get_project_role


def _object_project(obj):
    return obj.project if hasattr(obj, "project") else obj


class IsDocumentWriterOrReadOnly(BasePermission):
    """Members may read; only PROJECT_WRITE_ROLES may create/modify."""

    def has_object_permission(self, request, view, obj):
        project = _object_project(obj)
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in PROJECT_WRITE_ROLES
