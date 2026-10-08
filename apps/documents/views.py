from typing import ClassVar

from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.documents import selectors, services
from apps.documents.models import Document, DocumentFolder
from apps.documents.permissions import IsDocumentWriterOrReadOnly
from apps.documents.serializers import (
    DocumentFolderSerializer,
    DocumentSerializer,
    DocumentVersionUploadSerializer,
)


@extend_schema(tags=["documents"])
class FolderViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    GET   /api/folders/{id}/
    PATCH /api/folders/{id}/

    Listing/creating folders happens via /api/projects/{id}/folders/.
    """

    serializer_class = DocumentFolderSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsDocumentWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "head", "options"]
    queryset = DocumentFolder.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.folder_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        folder = self.get_object()
        serializer = self.get_serializer(folder, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(folder, field, value)
        folder.save()
        return Response(self.get_serializer(folder).data)


@extend_schema(tags=["documents"])
class DocumentViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    GET   /api/documents/{id}/
    PATCH /api/documents/{id}/               metadata only — never the file
    GET   /api/documents/{id}/download/       streams the CURRENT file for
                                               this specific version row
    GET   /api/documents/{id}/versions/       every version in this document's group
    POST  /api/documents/{id}/versions/       upload a new version

    Listing/creating documents happens via /api/projects/{id}/documents/.
    """

    serializer_class = DocumentSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsDocumentWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "post", "head", "options"]
    queryset = Document.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.document_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        document = self.get_object()
        serializer = self.get_serializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        document = services.update_document(document=document, data=serializer.validated_data)
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        document = self.get_object()
        response = FileResponse(
            document.file.open("rb"),
            content_type=document.content_type or "application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{document.original_filename}"'
        )
        return response

    @extend_schema(
        methods=["GET"], responses=DocumentSerializer(many=True), tags=["documents"]
    )
    @extend_schema(
        methods=["POST"],
        request=DocumentVersionUploadSerializer,
        responses={201: DocumentSerializer},
        tags=["documents"],
    )
    @action(detail=True, methods=["get", "post"], url_path="versions")
    def versions(self, request, pk=None):
        document = self.get_object()

        if request.method == "POST":
            serializer = DocumentVersionUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            new_version = services.create_new_version(
                previous=document,
                uploaded_by=request.user,
                uploaded_file=serializer.validated_data["file"],
                change_notes=serializer.validated_data.get("change_notes", ""),
            )
            return Response(
                DocumentSerializer(new_version).data, status=status.HTTP_201_CREATED
            )

        history = selectors.versions_of(document)
        return Response(DocumentSerializer(history, many=True).data)
