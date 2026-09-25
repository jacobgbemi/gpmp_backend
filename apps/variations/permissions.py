"""
Variation permission logic.

Reuses the same project-role resolution as `apps.projects.permissions` —
there is exactly one place (`get_project_role`) that answers "what role
does this user have on this project's organization."
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.models import ADMIN_ROLES, Role
from apps.projects.permissions import PROJECT_WRITE_ROLES, get_project_role

# Roles allowed to approve a variation. PROJECT_MANAGER is deliberately
# excluded — the same separation-of-duties rationale as payment review
# (PAYMENT_REVIEW_ROLES in apps.projects.permissions): the person managing
# delivery of a project should not also be the one who approves its cost
# increases.
VARIATION_APPROVAL_ROLES = ADMIN_ROLES | {Role.PROJECT_CONTROLS}


class IsVariationWriterOrReadOnly(BasePermission):
    """Members may read; only PROJECT_WRITE_ROLES may create/modify."""

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in PROJECT_WRITE_ROLES


class CanApproveVariation(BasePermission):
    """Object-level: only VARIATION_APPROVAL_ROLES may act on /approve/."""

    def has_object_permission(self, request, view, obj):
        role = get_project_role(request.user, obj.project)
        if role is None:
            return False
        return role in VARIATION_APPROVAL_ROLES
