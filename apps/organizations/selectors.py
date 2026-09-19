"""Read-side queries. Every organization lookup goes through the user."""

from django.db.models import OuterRef, QuerySet, Subquery

from apps.organizations.models import Organization, OrganizationMembership


def organizations_for_user(user) -> QuerySet[Organization]:
    """
    Organizations the user belongs to, annotated with the user's role.

    This is the ONLY queryset the API layer uses for organization access, so
    organizations the user is not a member of are simply invisible (404,
    never 403) — this prevents IDOR and existence probing.
    """
    if not getattr(user, "is_authenticated", False):
        return Organization.objects.none()

    role_subquery = OrganizationMembership.objects.filter(
        organization=OuterRef("pk"), user=user
    ).values("role")[:1]

    return (
        Organization.objects.filter(memberships__user=user)
        .annotate(my_role=Subquery(role_subquery))
        .distinct()
        .order_by("name")
    )


def members_of_organization(
    organization: Organization,
) -> QuerySet[OrganizationMembership]:
    return organization.memberships.select_related("user").order_by("user__email")