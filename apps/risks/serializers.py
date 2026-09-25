from typing import ClassVar

from rest_framework import serializers

from apps.accounts.models import User
from apps.risks.models import Issue, Risk


def _owner_queryset(project):
    if project is None:
        return User.objects.none()
    return User.objects.filter(
        memberships__organization=project.organization
    ).distinct()


class RiskSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    risk_level = serializers.SerializerMethodField()

    class Meta:
        model = Risk
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "description",
            "category",
            "probability",
            "impact",
            "risk_score",
            "risk_level",
            "response",
            "mitigation",
            "contingency",
            "owner",
            "owner_email",
            "status",
            "target_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "risk_score",
            "risk_level",
            "owner_email",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project") or getattr(self.instance, "project", None)
        self.fields["owner"].queryset = _owner_queryset(project)

    def get_risk_level(self, obj):
        # Standard 5x5 risk-matrix banding of a 1-25 probability*impact score.
        score = obj.risk_score
        if score >= 15:
            return "CRITICAL"
        if score >= 8:
            return "HIGH"
        if score >= 4:
            return "MEDIUM"
        return "LOW"


class IssueSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Issue
        fields: ClassVar[list[str]] = [
            "id",
            "title",
            "description",
            "severity",
            "owner",
            "owner_email",
            "status",
            "target_date",
            "resolution",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "owner_email",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project") or getattr(self.instance, "project", None)
        self.fields["owner"].queryset = _owner_queryset(project)
