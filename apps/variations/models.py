"""
Stage 3 — Variations.

A `Variation` tracks a proposed change to project scope/cost and its
journey through review to approval. The core rule (see README "approved
variation rule"): only a variation whose `status` has reached `APPROVED`
(or later — `IMPLEMENTED`, `CLOSED`) ever contributes to the project's
*approved* financial exposure. `PROPOSED`, `UNDER_REVIEW`, and `REJECTED`
variations are visible (so the owner can see what's being discussed) but
never counted as committed cost — see `apps.projects.selectors` for where
this distinction is applied on the project dashboard.
"""

from typing import ClassVar

from django.conf import settings
from django.db import models

from common.models import BaseModel
from common.validators import MONEY_VALIDATORS


class VariationCategory(models.TextChoices):
    SCOPE_CHANGE = "SCOPE_CHANGE", "Scope change"
    DESIGN_CHANGE = "DESIGN_CHANGE", "Design change"
    SITE_CONDITION = "SITE_CONDITION", "Site condition"
    CLIENT_REQUEST = "CLIENT_REQUEST", "Client request"
    REGULATORY = "REGULATORY", "Regulatory"
    MATERIAL_SUBSTITUTION = "MATERIAL_SUBSTITUTION", "Material substitution"
    ERROR_OMISSION = "ERROR_OMISSION", "Error or omission"
    OTHER = "OTHER", "Other"


class VariationStatus(models.TextChoices):
    PROPOSED = "PROPOSED", "Proposed"
    UNDER_REVIEW = "UNDER_REVIEW", "Under review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    IMPLEMENTED = "IMPLEMENTED", "Implemented"
    CLOSED = "CLOSED", "Closed"


# Statuses whose approved_amount counts as real, approved financial impact
# on the project — never PROPOSED, UNDER_REVIEW, or REJECTED.
VARIATION_APPROVED_STATUSES = frozenset(
    {VariationStatus.APPROVED, VariationStatus.IMPLEMENTED, VariationStatus.CLOSED}
)

# Statuses representing exposure that has NOT yet become approved cost —
# what the project *might* cost if these are approved.
VARIATION_PENDING_STATUSES = frozenset(
    {VariationStatus.PROPOSED, VariationStatus.UNDER_REVIEW}
)

# Legal status transitions via the generic PATCH. Approving specifically
# (PROPOSED/UNDER_REVIEW -> APPROVED) only happens through the dedicated
# /approve/ action (apps.variations.services.approve_variation), which
# enforces its own narrower authority — it is deliberately NOT reachable
# through this table.
VARIATION_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    VariationStatus.PROPOSED: frozenset({VariationStatus.UNDER_REVIEW, VariationStatus.REJECTED}),
    VariationStatus.UNDER_REVIEW: frozenset({VariationStatus.REJECTED}),
    VariationStatus.APPROVED: frozenset({VariationStatus.IMPLEMENTED, VariationStatus.CLOSED}),
    VariationStatus.REJECTED: frozenset({VariationStatus.CLOSED}),
    VariationStatus.IMPLEMENTED: frozenset({VariationStatus.CLOSED}),
}


class Variation(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="variations"
    )
    variation_number = models.CharField(max_length=30)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    category = models.CharField(
        max_length=32, choices=VariationCategory.choices, default=VariationCategory.OTHER
    )

    # Three independent amounts — never collapsed — mirroring the
    # requested/recommended/approved pattern established for payments.
    requested_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS
    )
    estimated_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, null=True, blank=True
    )
    approved_amount = models.DecimalField(
        max_digits=16, decimal_places=2, validators=MONEY_VALIDATORS, null=True, blank=True
    )

    status = models.CharField(
        max_length=16, choices=VariationStatus.choices, default=VariationStatus.PROPOSED
    )

    requested_date = models.DateField()
    approved_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # PROTECT: authorship/approval is part of the audit trail.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_variations",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_variations",
        null=True,
        blank=True,
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["project", "variation_number"],
                name="variations_variation_project_number_unique",
            ),
        ]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self):
        return f"{self.variation_number} ({self.status})"
