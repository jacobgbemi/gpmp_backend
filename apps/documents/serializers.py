from typing import ClassVar

from rest_framework import serializers

from apps.documents.models import Document, DocumentFolder


class DocumentFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFolder
        fields: ClassVar[list[str]] = [
            "id",
            "parent",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project") or getattr(self.instance, "project", None)
        if project is not None:
            self.fields["parent"].queryset = project.document_folders.all()


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields: ClassVar[list[str]] = [
            "id",
            "folder",
            "name",
            "description",
            "document_type",
            "status",
            "file",
            "original_filename",
            "content_type",
            "file_size",
            "download_url",
            "document_group",
            "version",
            "is_latest",
            "change_notes",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "original_filename",
            "content_type",
            "file_size",
            "download_url",
            "document_group",
            "version",
            "is_latest",
            "uploaded_by_email",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project") or getattr(self.instance, "project", None)
        if project is not None:
            self.fields["folder"].queryset = project.document_folders.all()
        if self.instance is not None:
            # file is only accepted at creation and via the dedicated
            # /versions/ action — never via a metadata PATCH.
            self.fields.pop("file", None)
            self.fields["change_notes"].read_only = True

    def get_download_url(self, obj):
        # Deliberately NOT obj.file.url — see README "file security
        # review": every byte is streamed through an authenticated view.
        return f"/api/documents/{obj.id}/download/"


class DocumentVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    change_notes = serializers.CharField(required=False, allow_blank=True, default="")
