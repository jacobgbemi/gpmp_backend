"""
Foundation DRF permission classes.

Role-based and organization-isolation permissions (IsOrganizationMember,
IsOrganizationAdmin, role checks, etc.) belong to the `accounts` /
`organizations` apps introduced in a later stage — they need the
OrganizationMembership model, which does not exist yet in Stage 0.

`IsAuthenticatedOrReadOnlyHealth` below is a narrow, foundation-only
exception used solely by the public health check endpoint.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticatedOrReadOnlyHealth(BasePermission):
    """Allow unauthenticated GET access (used only by /api/health/)."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS