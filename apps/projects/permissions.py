"""
Project-level permission logic.

Every permission here resolves the requester's role via their
`OrganizationMembership` on the project's organization — never via
anything the client supplied in the request. A project belonging to an
organization the user isn't a member of is invisible (404), never merely
forbidden (403) — see `apps.projects.selectors.projects_for_user`.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.models import ADMIN_ROLES, Role
from apps.organizations.permissions import get_role

# Roles allowed to create/modify projects, budgets, and progress updates.
PROJECT_WRITE_ROLES = ADMIN_ROLES | {Role.PROJECT_MANAGER, Role.PROJECT_CONTROLS}

# Roles allowed to act on a payment review. PROJECT_MANAGER is deliberately
# excluded — separation of duties: the person managing delivery of a
# project should not also be the one recommending/approving its payments.
PAYMENT_REVIEW_ROLES = ADMIN_ROLES | {Role.PROJECT_CONTROLS}


def get_project_role(user, project):
    return get_role(user, project.organization)


class IsProjectOrgMember(BasePermission):
    """Object-level: the requester belongs to the project's organization."""

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        return get_project_role(request.user, project) is not None


class IsProjectWriterOrReadOnly(BasePermission):
    """Members may read; only PROJECT_WRITE_ROLES may create/modify."""

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        role = get_project_role(request.user, project)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in PROJECT_WRITE_ROLES


class CanReviewPayment(BasePermission):
    """Object-level: only PAYMENT_REVIEW_ROLES may act on /review/."""

    def has_object_permission(self, request, view, obj):
        role = get_project_role(request.user, obj.project)
        if role is None:
            return False
        return role in PAYMENT_REVIEW_ROLES
