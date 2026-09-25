from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.risks import selectors, services
from apps.risks.models import Issue, Risk
from apps.risks.permissions import IsIssueWriterOrReadOnly, IsRiskWriterOrReadOnly
from apps.risks.serializers import IssueSerializer, RiskSerializer


@extend_schema(tags=["risks"])
class RiskViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/risks/{id}/
    PATCH /api/risks/{id}/

    Listing/creating risks happens via /api/projects/{id}/risks/.
    """

    serializer_class = RiskSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsRiskWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "head", "options"]
    queryset = Risk.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.risk_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        risk = self.get_object()
        serializer = self.get_serializer(risk, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        risk = services.update_risk(risk=risk, data=serializer.validated_data)
        return Response(self.get_serializer(risk).data)


@extend_schema(tags=["issues"])
class IssueViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/issues/{id}/
    PATCH /api/issues/{id}/

    Listing/creating issues happens via /api/projects/{id}/issues/.
    """

    serializer_class = IssueSerializer
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, IsIssueWriterOrReadOnly]
    http_method_names: ClassVar[list[str]] = ["get", "patch", "head", "options"]
    queryset = Issue.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.issue_queryset_for_user(self.request.user)

    def partial_update(self, request, *args, **kwargs):
        issue = self.get_object()
        serializer = self.get_serializer(issue, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        issue = services.update_issue(issue=issue, data=serializer.validated_data)
        return Response(self.get_serializer(issue).data)
