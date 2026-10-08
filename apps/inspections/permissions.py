"""
Inspection/Evidence permission logic.

`INSPECTION_WRITE_ROLES` extends `PROJECT_WRITE_ROLES` with
`SITE_INSPECTOR` — the first place in this codebase that role actually
grants any write access. It's the obvious fit: a site inspector should be
able to run inspections and capture evidence without needing
`PROJECT_MANAGER`/`PROJECT_CONTROLS`/admin privileges over the rest of the
project.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.models import Role
from apps.projects.permissions import PROJECT_WRITE_ROLES, get_project_role

INSPECTION_WRITE_ROLES = PROJECT_WRITE_ROLES | {Role.SITE_INSPECTOR}


def _object_project(obj):
    if hasattr(obj, "project"):
        return obj.project
    if hasattr(obj, "inspection"):
        return obj.inspection.project
    return obj


class IsInspectionWriterOrReadOnly(BasePermission):
    """Members may read; only INSPECTION_WRITE_ROLES may create/modify."""

    def has_object_permission(self, request, view, obj):
        project = _object_project(obj)
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in INSPECTION_WRITE_ROLES
