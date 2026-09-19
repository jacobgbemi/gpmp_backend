from django.conf import settings
from django.db import models

from common.models import BaseModel


class Role(models.TextChoices):
    PLATFORM_ADMIN = "PLATFORM_ADMIN", "Platform admin"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN", "Organization admin"
    PROJECT_MANAGER = "PROJECT_MANAGER", "Project manager"
    PROJECT_CONTROLS = "PROJECT_CONTROLS", "Project controls"
    SITE_INSPECTOR = "SITE_INSPECTOR", "Site inspector"
    CONSULTANT = "CONSULTANT", "Consultant"
    CLIENT_OWNER = "CLIENT_OWNER", "Client owner"
    VIEWER = "VIEWER", "Viewer"


# Roles allowed to change organization settings and manage its members.
ADMIN_ROLES = frozenset({Role.PLATFORM_ADMIN, Role.ORGANIZATION_ADMIN})


class Organization(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrganizationMembership(BaseModel):
    # CASCADE: a membership is a pure join record and has no meaning without
    # both its user and its organization.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        ordering = ["organization__name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"],
                name="organizations_membership_user_org_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"