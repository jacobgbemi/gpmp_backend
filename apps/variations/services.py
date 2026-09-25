"""
Write-side business logic for variations.

`approve_variation` is the one and only path by which a variation's
`status` can become `APPROVED` — it is deliberately not reachable through
the generic `update_variation` status-transition table, so "who approved
this and when" and "does the approved_amount actually get set" can never
be bypassed by a plain PATCH.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.variations.models import (
    VARIATION_STATUS_TRANSITIONS,
    Variation,
    VariationStatus,
)

# Variations may only be approved from these statuses.
_APPROVABLE_FROM = frozenset({VariationStatus.PROPOSED, VariationStatus.UNDER_REVIEW})


@transaction.atomic
def create_variation(*, project, created_by, **fields) -> Variation:
    fields.setdefault("requested_date", timezone.now().date())
    try:
        return Variation.objects.create(project=project, created_by=created_by, **fields)
    except IntegrityError as exc:
        raise ValidationError(
            {
                "variation_number": (
                    "A variation with this number already exists for this project."
                )
            }
        ) from exc


@transaction.atomic
def update_variation(*, variation: Variation, data: dict) -> Variation:
    new_status = data.get("status")
    if new_status and new_status != variation.status:
        if new_status == VariationStatus.APPROVED:
            raise ValidationError(
                {
                    "status": (
                        "Use POST /api/variations/{id}/approve/ to approve a "
                        "variation — it cannot be set directly."
                    )
                }
            )
        allowed = VARIATION_STATUS_TRANSITIONS.get(variation.status, frozenset())
        if new_status not in allowed:
            raise ValidationError(
                {
                    "status": (
                        f"Cannot transition variation from '{variation.status}' to "
                        f"'{new_status}'."
                    )
                }
            )

    for field, value in data.items():
        setattr(variation, field, value)

    try:
        variation.full_clean()
        variation.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    except IntegrityError as exc:
        raise ValidationError(
            {
                "variation_number": (
                    "A variation with this number already exists for this project."
                )
            }
        ) from exc
    return variation


@transaction.atomic
def approve_variation(
    *, variation: Variation, approver, approved_amount: Decimal, notes: str = ""
) -> Variation:
    if variation.status not in _APPROVABLE_FROM:
        raise ValidationError(
            {
                "status": (
                    f"Cannot approve a variation while status is '{variation.status}'. "
                    f"Only PROPOSED or UNDER_REVIEW variations may be approved."
                )
            }
        )
    if approved_amount is None or approved_amount < 0:
        raise ValidationError({"approved_amount": "A non-negative approved amount is required."})

    variation.approved_amount = approved_amount
    variation.approved_by = approver
    variation.approved_date = timezone.now().date()
    variation.status = VariationStatus.APPROVED
    if notes:
        variation.notes = notes
    variation.save()
    return variation
