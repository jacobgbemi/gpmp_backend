from typing import ClassVar

from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inspections import selectors, services
from apps.inspections.models import Inspection, InspectionItem, ProjectEvidence
from apps.inspections.permissions import IsInspectionWriterOrReadOnly
from apps.inspections.serializers import (
    InspectionItemSerializer,
    InspectionSerializer,
    ProjectEvidenceSerializer,
)


@extend_schema(tags=["inspections"])
class InspectionViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    GET   /api/inspections/{id}/
    PATCH /api/inspections/{id}/                 status changes other than completion
    GET   /api/inspections/{id}/items/
    POST  /api/inspections/{id}/items/            add an inspection item
    POST  /api/inspections/{id}/complete/         the only way to reach COMPLETED

    Listing/creating inspections happens via /api/projects/{id}/inspections/.
    """

    serializer_class = InspectionSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsInspectionWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "post", "head", "options"]
    queryset = Inspection.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.inspection_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        inspection = self.get_object()
        serializer = self.get_serializer(inspection, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        inspection = services.update_inspection(
            inspection=inspection, data=serializer.validated_data
        )
        return Response(self.get_serializer(inspection).data)

    @extend_schema(
        methods=["GET"], responses=InspectionItemSerializer(many=True), tags=["inspections"]
    )
    @extend_schema(
        methods=["POST"],
        request=InspectionItemSerializer,
        responses={201: InspectionItemSerializer},
        tags=["inspections"],
    )
    @action(detail=True, methods=["get", "post"], url_path="items")
    def items(self, request, pk=None):
        inspection = self.get_object()

        if request.method == "POST":
            serializer = InspectionItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            item = services.add_inspection_item(
                inspection=inspection, **serializer.validated_data
            )
            return Response(
                InspectionItemSerializer(item).data, status=status.HTTP_201_CREATED
            )

        queryset = selectors.items_for_inspection(inspection)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        page = self.paginate_queryset(queryset)
        serializer = InspectionItemSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(responses={200: InspectionSerializer})
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        inspection = self.get_object()
        inspection = services.complete_inspection(inspection=inspection)
        return Response(InspectionSerializer(inspection).data)


@extend_schema(tags=["inspections"])
class InspectionItemViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    GET   /api/inspection-items/{id}/
    PATCH /api/inspection-items/{id}/   locked once the parent inspection is COMPLETED
    """

    serializer_class = InspectionItemSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsInspectionWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "head", "options"]
    queryset = InspectionItem.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.inspection_item_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = services.update_inspection_item(item=item, data=serializer.validated_data)
        return Response(self.get_serializer(item).data)


@extend_schema(tags=["evidence"])
class EvidenceViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET /api/evidence/{id}/
    GET /api/evidence/{id}/download/   the ONLY way to fetch the file itself —
                                        streamed through this permission-checked
                                        view, never a direct storage URL.

    Listing/creating evidence happens via /api/projects/{id}/evidence/.
    """

    serializer_class = ProjectEvidenceSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsInspectionWriterOrReadOnly]
    queryset = ProjectEvidence.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.evidence_queryset_for_user(self.request.user)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        evidence = self.get_object()
        response = FileResponse(
            evidence.file.open("rb"),
            content_type=evidence.content_type or "application/octet-stream",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{evidence.original_filename}"'
        )
        return response
