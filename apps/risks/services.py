"""
Write-side business logic for risks and issues.

`_score` is the single place `risk_score` is ever computed — it is always
`probability * impact`, recomputed on every create/update that touches
either input, so it can never drift out of sync with them (same principle
as budget totals in apps.projects.selectors never being stored).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.projects.permissions import get_project_role
from apps.risks.models import (
    ISSUE_STATUS_TRANSITIONS,
    RISK_STATUS_TRANSITIONS,
    Issue,
    IssueStatus,
    Risk,
)


def _score(probability: int, impact: int) -> int:
    return probability * impact


def _validate_owner_is_project_member(*, owner, project) -> None:
    if get_project_role(owner, project) is None:
        raise ValidationError(
            {"owner": "The owner must be a member of the project's organization."}
        )


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------


@transaction.atomic
def create_risk(*, project, owner, probability: int, impact: int, **fields) -> Risk:
    _validate_owner_is_project_member(owner=owner, project=project)
    risk = Risk(
        project=project,
        owner=owner,
        probability=probability,
        impact=impact,
        risk_score=_score(probability, impact),
        **fields,
    )
    try:
        risk.full_clean()
        risk.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return risk


@transaction.atomic
def update_risk(*, risk: Risk, data: dict) -> Risk:
    new_status = data.get("status")
    if new_status and new_status != risk.status:
        allowed = RISK_STATUS_TRANSITIONS.get(risk.status, frozenset())
        if new_status not in allowed:
            raise ValidationError(
                {
                    "status": (
                        f"Cannot transition risk from '{risk.status}' to '{new_status}'."
                    )
                }
            )

    if "owner" in data:
        _validate_owner_is_project_member(owner=data["owner"], project=risk.project)

    for field, value in data.items():
        setattr(risk, field, value)

    if "probability" in data or "impact" in data:
        risk.risk_score = _score(risk.probability, risk.impact)

    try:
        risk.full_clean()
        risk.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return risk


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------


@transaction.atomic
def create_issue(*, project, owner, **fields) -> Issue:
    _validate_owner_is_project_member(owner=owner, project=project)
    issue = Issue(project=project, owner=owner, **fields)
    try:
        issue.full_clean()
        issue.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return issue


@transaction.atomic
def update_issue(*, issue: Issue, data: dict) -> Issue:
    new_status = data.get("status")
    if new_status and new_status != issue.status:
        allowed = ISSUE_STATUS_TRANSITIONS.get(issue.status, frozenset())
        if new_status not in allowed:
            raise ValidationError(
                {"status": f"Cannot transition issue from '{issue.status}' to '{new_status}'."}
            )
        if new_status == IssueStatus.RESOLVED and not (data.get("resolution") or issue.resolution):
            raise ValidationError(
                {"resolution": "A resolution is required to mark an issue resolved."}
            )

    if "owner" in data:
        _validate_owner_is_project_member(owner=data["owner"], project=issue.project)

    for field, value in data.items():
        setattr(issue, field, value)

    try:
        issue.full_clean()
        issue.save()
    except DjangoValidationError as exc:
        raise ValidationError(
            exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        ) from exc
    return issue
