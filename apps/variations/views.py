from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.variations import selectors, services
from apps.variations.models import Variation
from apps.variations.permissions import CanApproveVariation, IsVariationWriterOrReadOnly
from apps.variations.serializers import VariationApproveSerializer, VariationSerializer


@extend_schema(tags=["variations"])
class VariationViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """
    GET   /api/variations/{id}/
    PATCH /api/variations/{id}/                 status changes other than approval
    POST  /api/variations/{id}/approve/          the only way to reach APPROVED

    Listing/creating variations happens via /api/projects/{id}/variations/.
    """

    serializer_class = VariationSerializer
    queryset = Variation.objects.none()  # overridden by get_queryset
    http_method_names: ClassVar[list[str]] = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        return selectors.variation_queryset_for_user(self.request.user)

    def get_permissions(self):
        if self.action == "approve":
            return [IsAuthenticated(), CanApproveVariation()]
        return [IsAuthenticated(), IsVariationWriterOrReadOnly()]

    def partial_update(self, request, *args, **kwargs):
        variation = self.get_object()
        serializer = self.get_serializer(variation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        variation = services.update_variation(
            variation=variation, data=serializer.validated_data
        )
        return Response(self.get_serializer(variation).data)

    @extend_schema(
        request=VariationApproveSerializer, responses={200: VariationSerializer}
    )
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        variation = self.get_object()
        serializer = VariationApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variation = services.approve_variation(
            variation=variation,
            approver=request.user,
            approved_amount=serializer.validated_data["approved_amount"],
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(VariationSerializer(variation).data)
