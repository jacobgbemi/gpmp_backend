from typing import ClassVar

from rest_framework import serializers

from apps.accounts.models import User
from apps.inspections.models import Inspection, InspectionItem, ProjectEvidence


def _member_queryset(project):
    if project is None:
        return User.objects.none()
    return User.objects.filter(memberships__organization=project.organization).distinct()


class InspectionSerializer(serializers.ModelSerializer):
    inspector_email = serializers.EmailField(source="inspector.email", read_only=True)

    class Meta:
        model = Inspection
        fields: ClassVar[list[str]] = [
            "id",
            "inspection_type",
            "inspection_date",
            "inspector",
            "inspector_email",
            "location",
            "summary",
            "status",
            "overall_status",
            "recommendations",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "inspector_email",
            "overall_status",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project") or getattr(self.instance, "project", None)
        self.fields["inspector"].queryset = _member_queryset(project)
        if self.instance is None:
            # Creating: status always starts SCHEDULED.
            self.fields["status"].read_only = True


class InspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields: ClassVar[list[str]] = [
            "id",
            "category",
            "description",
            "status",
            "severity",
            "recommendation",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]


class ProjectEvidenceSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)

    class Meta:
        model = ProjectEvidence
        fields: ClassVar[list[str]] = [
            "id",
            "inspection",
            "title",
            "description",
            "evidence_type",
            "file",
            "original_filename",
            "content_type",
            "file_size",
            "download_url",
            "captured_at",
            "latitude",
            "longitude",
            "metadata",
            "uploaded_by_email",
            "created_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "original_filename",
            "content_type",
            "file_size",
            "download_url",
            "uploaded_by_email",
            "created_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is not None:
            self.fields["inspection"].queryset = project.inspections.all()

    def get_download_url(self, obj):
        # Deliberately NOT obj.file.url — see README "file security
        # review": every byte is streamed through an authenticated view,
        # never a direct (and potentially public) storage URL.
        return f"/api/evidence/{obj.id}/download/"
