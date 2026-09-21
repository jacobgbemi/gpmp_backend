from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.permissions import get_role
from apps.projects import selectors, services
from apps.projects.models import PaymentApplication
from apps.projects.permissions import (
    PROJECT_WRITE_ROLES,
    CanReviewPayment,
    IsProjectOrgMember,
    IsProjectWriterOrReadOnly,
)
from apps.projects.serializers import (
    BudgetItemSerializer,
    DashboardSerializer,
    PaymentApplicationSerializer,
    PaymentReviewSerializer,
    ProgressUpdateSerializer,
    ProjectBudgetSerializer,
    ProjectSerializer,
)


@extend_schema(tags=["projects"])
class ProjectViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/projects/                projects in the user's organizations
    POST   /api/projects/                 create (write roles only)
    GET    /api/projects/{id}/
    PATCH  /api/projects/{id}/            write roles only
    DELETE /api/projects/{id}/            write roles only; blocked once real
                                           money has moved on the project
    GET    /api/projects/{id}/budget/
    POST   /api/projects/{id}/budget/     add a budget line item
    GET    /api/projects/{id}/progress/
    POST   /api/projects/{id}/progress/   append a progress update
    GET    /api/projects/{id}/payments/
    POST   /api/projects/{id}/payments/   submit a payment application
    GET    /api/projects/{id}/dashboard/

    Projects in an organization the user doesn't belong to are absent from
    the queryset entirely, so they 404 — never 403.
    """

    serializer_class = ProjectSerializer
    permission_classes: ClassVar[list[type]] = [
        IsAuthenticated,
        IsProjectWriterOrReadOnly,
    ]
    http_method_names: ClassVar[list[str]] = [
        "get",
        "post",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def get_queryset(self):
        return selectors.projects_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.validated_data["organization"]

        if get_role(request.user, organization) not in PROJECT_WRITE_ROLES:
            raise PermissionDenied(
                "You do not have permission to create projects in this organization."
            )

        data = dict(serializer.validated_data)
        data.pop("organization")
        project = services.create_project(organization=organization, **data)
        return Response(
            self.get_serializer(project).data, status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        project = self.get_object()
        serializer = self.get_serializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("organization", None)
        project = services.update_project(project=project, data=data)
        return Response(self.get_serializer(project).data)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        services.delete_project(project=project)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["GET"], responses=ProjectBudgetSerializer, tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=BudgetItemSerializer,
        responses={201: BudgetItemSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="budget")
    def budget(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = BudgetItemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            item = services.add_budget_item(
                project=project, **serializer.validated_data
            )
            return Response(
                BudgetItemSerializer(item).data, status=status.HTTP_201_CREATED
            )

        _budget, items = selectors.budget_items_for_project(project)
        totals = selectors.project_dashboard(project)
        payload = {
            "items": items,
            "original_total": totals["original_budget"],
            "approved_total": totals["approved_budget"],
            "committed_total": totals["committed_cost"],
            "actual_total": totals["actual_spend"],
        }
        return Response(ProjectBudgetSerializer(payload).data)

    @extend_schema(
        methods=["GET"],
        responses=ProgressUpdateSerializer(many=True),
        tags=["projects"],
    )
    @extend_schema(
        methods=["POST"],
        request=ProgressUpdateSerializer,
        responses={201: ProgressUpdateSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="progress")
    def progress(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = ProgressUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            update = services.add_progress_update(
                project=project, submitted_by=request.user, **serializer.validated_data
            )
            return Response(
                ProgressUpdateSerializer(update).data, status=status.HTTP_201_CREATED
            )

        updates = selectors.progress_updates_for_project(project)
        page = self.paginate_queryset(updates)
        serializer = ProgressUpdateSerializer(
            page if page is not None else updates, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"],
        responses=PaymentApplicationSerializer(many=True),
        tags=["projects"],
    )
    @extend_schema(
        methods=["POST"],
        request=PaymentApplicationSerializer,
        responses={201: PaymentApplicationSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="payments")
    def payments(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = PaymentApplicationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            payment = services.create_payment(
                project=project, submitted_by=request.user, **serializer.validated_data
            )
            return Response(
                PaymentApplicationSerializer(payment).data,
                status=status.HTTP_201_CREATED,
            )

        payments_qs = selectors.payments_for_project(project)
        page = self.paginate_queryset(payments_qs)
        serializer = PaymentApplicationSerializer(
            page if page is not None else payments_qs, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(responses=DashboardSerializer, tags=["projects"])
    @action(detail=True, methods=["get"], url_path="dashboard")
    def dashboard(self, request, pk=None):
        project = self.get_object()
        data = selectors.project_dashboard(project)
        return Response(DashboardSerializer(data).data)


@extend_schema(tags=["payments"])
class PaymentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/payments/{id}/
    POST /api/payments/{id}/review/   move a payment through its lifecycle

    Listing/creating payments happens via /api/projects/{id}/payments/ —
    this resource is for direct lookup and review of a single payment.
    """

    serializer_class = PaymentApplicationSerializer
    queryset = PaymentApplication.objects.none()  # overridden by get_queryset

    def get_queryset(self):
        return selectors.payment_queryset_for_user(self.request.user)

    def get_permissions(self):
        if self.action == "review":
            return [IsAuthenticated(), CanReviewPayment()]
        return [IsAuthenticated(), IsProjectOrgMember()]

    @extend_schema(
        request=PaymentReviewSerializer, responses={200: PaymentApplicationSerializer}
    )
    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        payment = self.get_object()
        serializer = PaymentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = services.PaymentService.review(
            payment=payment,
            reviewer=request.user,
            decision=serializer.validated_data["decision"],
            amount=serializer.validated_data.get("amount"),
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(PaymentApplicationSerializer(payment).data)
