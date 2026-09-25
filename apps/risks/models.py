"""
Stage 3 — Risks and Issues.

`Risk.risk_score` is always `probability × impact`, computed server-side
in `apps.risks.services` — it is never a value the client sets directly
(see README "risk scoring formula"). `Issue` is a deliberately separate
model from `Risk`: a risk is a *potential* future problem being tracked
and mitigated; an issue is something that has already happened and needs
resolving. Nothing here auto-converts one into the other.
"""

from typing import ClassVar

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import BaseModel


class RiskCategory(models.TextChoices):
    COST = "COST", "Cost"
    SCHEDULE = "SCHEDULE", "Schedule"
    QUALITY = "QUALITY", "Quality"
    PROCUREMENT = "PROCUREMENT", "Procurement"
    CONTRACTOR = "CONTRACTOR", "Contractor"
    DESIGN = "DESIGN", "Design"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    REGULATORY = "REGULATORY", "Regulatory"
    SAFETY = "SAFETY", "Safety"
    OTHER = "OTHER", "Other"


class RiskResponse(models.TextChoices):
    AVOID = "AVOID", "Avoid"
    MITIGATE = "MITIGATE", "Mitigate"
    TRANSFER = "TRANSFER", "Transfer"
    ACCEPT = "ACCEPT", "Accept"


class RiskStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    MITIGATING = "MITIGATING", "Mitigating"
    MONITORING = "MONITORING", "Monitoring"
    CLOSED = "CLOSED", "Closed"


RISK_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    RiskStatus.OPEN: frozenset({RiskStatus.MITIGATING, RiskStatus.MONITORING, RiskStatus.CLOSED}),
    RiskStatus.MITIGATING: frozenset({RiskStatus.MONITORING, RiskStatus.CLOSED}),
    RiskStatus.MONITORING: frozenset({RiskStatus.MITIGATING, RiskStatus.CLOSED}),
}

_SCORE_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class Risk(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="risks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=32, choices=RiskCategory.choices, default=RiskCategory.OTHER
    )

    probability = models.PositiveSmallIntegerField(validators=_SCORE_VALIDATORS)
    impact = models.PositiveSmallIntegerField(validators=_SCORE_VALIDATORS)
    # Always probability * impact (range 1-25). Recomputed server-side by
    # apps.risks.services whenever probability/impact change — never
    # client-writable directly.
    risk_score = models.PositiveSmallIntegerField(editable=False)

    response = models.CharField(
        max_length=16, choices=RiskResponse.choices, default=RiskResponse.MITIGATE
    )
    mitigation = models.TextField(blank=True)
    contingency = models.TextField(blank=True)

    # PROTECT: a risk must always have an accountable owner; deleting that
    # user must not silently orphan the risk.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_risks"
    )
    status = models.CharField(
        max_length=16, choices=RiskStatus.choices, default=RiskStatus.OPEN
    )
    target_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-risk_score", "-created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "-risk_score"]),
        ]

    def __str__(self):
        return f"{self.title} (score {self.risk_score})"


class IssueSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class IssueStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"


ISSUE_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    IssueStatus.OPEN: frozenset({IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED, IssueStatus.CLOSED}),
    IssueStatus.IN_PROGRESS: frozenset({IssueStatus.RESOLVED, IssueStatus.CLOSED}),
    IssueStatus.RESOLVED: frozenset({IssueStatus.IN_PROGRESS, IssueStatus.CLOSED}),
}

# Transitioning into RESOLVED requires a non-empty `resolution` — enforced
# in apps.risks.services, mirroring the payment REJECT-requires-notes rule.
_STATUSES_REQUIRING_RESOLUTION = frozenset({IssueStatus.RESOLVED})


class Issue(BaseModel):
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="issues"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=16, choices=IssueSeverity.choices, default=IssueSeverity.MEDIUM
    )
    # PROTECT: same audit-trail rationale as Risk.owner.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_issues"
    )
    status = models.CharField(
        max_length=16, choices=IssueStatus.choices, default=IssueStatus.OPEN
    )
    target_date = models.DateField(null=True, blank=True)
    resolution = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "severity"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"
