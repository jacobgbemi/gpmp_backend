"""
Centralized organization / role permission logic.

Views never inspect roles directly; they use these classes so the rules live
in one place.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.organizations.models import ADMIN_ROLES, OrganizationMembership


def get_role(user, organization):
    return (
        OrganizationMembership.objects.filter(user=user, organization=organization)
        .values_list("role", flat=True)
        .first()
    )


class IsOrganizationMember(BasePermission):
    """Object-level: the requester belongs to the organization."""

    def has_object_permission(self, request, view, obj):
        return get_role(request.user, obj) is not None


class IsOrganizationAdminOrReadOnly(BasePermission):
    """
    Object-level: members may read; only admin roles may modify.
    """

    def has_object_permission(self, request, view, obj):
        role = get_role(request.user, obj)
        if role is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in ADMIN_ROLES