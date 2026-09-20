"""Write-side business logic for organizations and memberships."""

from django.db import IntegrityError, transaction
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.organizations.models import Organization, OrganizationMembership, Role


def _unique_slug(name: str) -> str:
    base = slugify(name)[:70] or "organization"
    slug, counter = base, 2
    while Organization.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


@transaction.atomic
def create_organization(*, creator, name: str) -> Organization:
    """Create an organization; the creator becomes its ORGANIZATION_ADMIN."""
    organization = Organization.objects.create(
        name=name.strip(), slug=_unique_slug(name)
    )
    OrganizationMembership.objects.create(
        user=creator,
        organization=organization,
        role=Role.ORGANIZATION_ADMIN,
    )
    return organization


def add_member(
    *, organization: Organization, user, role: str = Role.VIEWER
) -> OrganizationMembership:
    if role not in Role.values:
        raise ValidationError({"role": f"Invalid role '{role}'."})
    try:
        with transaction.atomic():
            return OrganizationMembership.objects.create(
                user=user, organization=organization, role=role
            )
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "User is already a member of this organization."}
        ) from exc


def change_member_role(
    *, membership: OrganizationMembership, role: str
) -> OrganizationMembership:
    if role not in Role.values:
        raise ValidationError({"role": f"Invalid role '{role}'."})
    membership.role = role
    membership.save(update_fields=["role", "updated_at"])
    return membership
