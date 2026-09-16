"""
Shared abstract base models.

Every business-domain model introduced in later stages should inherit from
`UUIDModel` (public UUID identifier, per the architecture requirement) and
`TimeStampedModel` (created_at / updated_at audit fields), typically via the
combined `BaseModel`.

No concrete (non-abstract) models are defined here in Stage 0 — this module
exists purely as foundation for later business-domain apps.
"""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """
    Abstract base providing a UUID public identifier.

    The architecture requires UUIDs as public identifiers so internal
    database primary keys are never exposed to the frontend/API consumers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract base providing created_at / updated_at audit timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Standard base for business-domain models: UUID id + timestamps."""

    class Meta:
        abstract = True