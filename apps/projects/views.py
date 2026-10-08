from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.documents import selectors as document_selectors
from apps.documents import services as document_services
from apps.documents.serializers import DocumentFolderSerializer, DocumentSerializer
from apps.inspections import selectors as inspection_selectors
from apps.inspections import services as inspection_services
from apps.inspections.permissions import IsInspectionWriterOrReadOnly
from apps.inspections.serializers import InspectionSerializer, ProjectEvidenceSerializer
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
from apps.risks import selectors as risk_selectors
from apps.risks import services as risk_services
from apps.risks.serializers import IssueSerializer, RiskSerializer
from apps.variations import selectors as variation_selectors
from apps.variations import services as variation_services
from apps.variations.serializers import VariationSerializer


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
    GET    /api/projects/{id}/variations/
    POST   /api/projects/{id}/variations/ propose a variation
    GET    /api/projects/{id}/risks/
    POST   /api/projects/{id}/risks/      log a risk
    GET    /api/projects/{id}/issues/
    POST   /api/projects/{id}/issues/     log an issue
    GET    /api/projects/{id}/inspections/
    POST   /api/projects/{id}/inspections/ schedule an inspection
    GET    /api/projects/{id}/evidence/
    POST   /api/projects/{id}/evidence/   upload evidence (multipart)
    GET    /api/projects/{id}/folders/
    POST   /api/projects/{id}/folders/    create a document folder
    GET    /api/projects/{id}/documents/
    POST   /api/projects/{id}/documents/  upload a document (multipart)
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

    # The global DEFAULT_FILTER_BACKENDS (django-filter, SearchFilter,
    # OrderingFilter) only act on a view that declares the fields below;
    # without them `?search=` and `?status=` are silently ignored.
    filterset_fields: ClassVar[list[str]] = ["status", "project_type"]
    search_fields: ClassVar[list[str]] = [
        "name",
        "project_code",
        "location",
        "client_name",
    ]
    ordering_fields: ClassVar[list[str]] = [
        "created_at",
        "name",
        "contract_value",
        "planned_end_date",
    ]
    ordering: ClassVar[list[str]] = ["-created_at"]

    def get_queryset(self):
        return selectors.projects_for_user(self.request.user)

    def get_permissions(self):
        # The `inspections` and `evidence` sub-actions are the one place
        # SITE_INSPECTOR needs write access, even though it's outside
        # PROJECT_WRITE_ROLES — see apps.inspections.permissions. Every
        # other action keeps the standard project-level check.
        if self.action in ("inspections", "evidence"):
            return [IsAuthenticated(), IsInspectionWriterOrReadOnly()]
        return super().get_permissions()

    def filter_queryset(self, queryset):
        # Only the list endpoint is filterable. The detail and nested
        # actions (budget/progress/payments/dashboard) call get_object(),
        # which runs filter_queryset — so without this guard something like
        # /projects/{id}/payments/?status=PAID would filter the *project*
        # by status and 404.
        if self.action != "list":
            return queryset
        return super().filter_queryset(queryset)

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

    @extend_schema(
        methods=["GET"], responses=VariationSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=VariationSerializer,
        responses={201: VariationSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="variations")
    def variations(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = VariationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            variation = variation_services.create_variation(
                project=project, created_by=request.user, **serializer.validated_data
            )
            return Response(
                VariationSerializer(variation).data, status=status.HTTP_201_CREATED
            )

        queryset = variation_selectors.variations_for_project(project)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        category_filter = request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(category=category_filter)
        page = self.paginate_queryset(queryset)
        serializer = VariationSerializer(
            page if page is not None else queryset, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=RiskSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=RiskSerializer,
        responses={201: RiskSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="risks")
    def risks(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = RiskSerializer(data=request.data, context={"project": project})
            serializer.is_valid(raise_exception=True)
            risk = risk_services.create_risk(
                project=project, **serializer.validated_data
            )
            return Response(RiskSerializer(risk).data, status=status.HTTP_201_CREATED)

        queryset = risk_selectors.risks_for_project(project)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        category_filter = request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(category=category_filter)
        owner_filter = request.query_params.get("owner")
        if owner_filter:
            queryset = queryset.filter(owner_id=owner_filter)
        page = self.paginate_queryset(queryset)
        serializer = RiskSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=IssueSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=IssueSerializer,
        responses={201: IssueSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="issues")
    def issues(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = IssueSerializer(
                data=request.data, context={"project": project}
            )
            serializer.is_valid(raise_exception=True)
            issue = risk_services.create_issue(
                project=project, **serializer.validated_data
            )
            return Response(IssueSerializer(issue).data, status=status.HTTP_201_CREATED)

        queryset = risk_selectors.issues_for_project(project)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        severity_filter = request.query_params.get("severity")
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        owner_filter = request.query_params.get("owner")
        if owner_filter:
            queryset = queryset.filter(owner_id=owner_filter)
        page = self.paginate_queryset(queryset)
        serializer = IssueSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=InspectionSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=InspectionSerializer,
        responses={201: InspectionSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="inspections")
    def inspections(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = InspectionSerializer(data=request.data, context={"project": project})
            serializer.is_valid(raise_exception=True)
            inspection = inspection_services.create_inspection(
                project=project, **serializer.validated_data
            )
            return Response(
                InspectionSerializer(inspection).data, status=status.HTTP_201_CREATED
            )

        queryset = inspection_selectors.inspections_for_project(project)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        type_filter = request.query_params.get("inspection_type")
        if type_filter:
            queryset = queryset.filter(inspection_type=type_filter)
        page = self.paginate_queryset(queryset)
        serializer = InspectionSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=ProjectEvidenceSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=ProjectEvidenceSerializer,
        responses={201: ProjectEvidenceSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="evidence")
    def evidence(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = ProjectEvidenceSerializer(
                data=request.data, context={"project": project}
            )
            serializer.is_valid(raise_exception=True)
            data = dict(serializer.validated_data)
            uploaded_file = data.pop("file")
            evidence_type = data.pop("evidence_type")
            inspection = data.pop("inspection", None)
            evidence = inspection_services.create_evidence(
                project=project,
                uploaded_by=request.user,
                uploaded_file=uploaded_file,
                evidence_type=evidence_type,
                inspection=inspection,
                **data,
            )
            return Response(
                ProjectEvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED
            )

        inspection_filter = request.query_params.get("inspection")
        queryset = inspection_selectors.evidence_for_project(
            project, inspection_id=inspection_filter
        )
        type_filter = request.query_params.get("evidence_type")
        if type_filter:
            queryset = queryset.filter(evidence_type=type_filter)
        page = self.paginate_queryset(queryset)
        serializer = ProjectEvidenceSerializer(
            page if page is not None else queryset, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=DocumentFolderSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=DocumentFolderSerializer,
        responses={201: DocumentFolderSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="folders")
    def folders(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = DocumentFolderSerializer(
                data=request.data, context={"project": project}
            )
            serializer.is_valid(raise_exception=True)
            folder = document_services.create_folder(
                project=project, **serializer.validated_data
            )
            return Response(
                DocumentFolderSerializer(folder).data, status=status.HTTP_201_CREATED
            )

        queryset = document_selectors.folders_for_project(project)
        page = self.paginate_queryset(queryset)
        serializer = DocumentFolderSerializer(
            page if page is not None else queryset, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @extend_schema(
        methods=["GET"], responses=DocumentSerializer(many=True), tags=["projects"]
    )
    @extend_schema(
        methods=["POST"],
        request=DocumentSerializer,
        responses={201: DocumentSerializer},
        tags=["projects"],
    )
    @action(detail=True, methods=["get", "post"], url_path="documents")
    def documents(self, request, pk=None):
        project = self.get_object()

        if request.method == "POST":
            serializer = DocumentSerializer(data=request.data, context={"project": project})
            serializer.is_valid(raise_exception=True)
            data = dict(serializer.validated_data)
            uploaded_file = data.pop("file")
            document_type = data.pop("document_type")
            folder = data.pop("folder", None)
            document = document_services.create_document(
                project=project,
                uploaded_by=request.user,
                uploaded_file=uploaded_file,
                document_type=document_type,
                folder=folder,
                **data,
            )
            return Response(
                DocumentSerializer(document).data, status=status.HTTP_201_CREATED
            )

        folder_filter = request.query_params.get("folder")
        queryset = document_selectors.documents_for_project(project, folder_id=folder_filter)
        type_filter = request.query_params.get("document_type")
        if type_filter:
            queryset = queryset.filter(document_type=type_filter)
        page = self.paginate_queryset(queryset)
        serializer = DocumentSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


@extend_schema(tags=["payments"])
class PaymentViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET   /api/payments/{id}/
    PATCH /api/payments/{id}/          correct amount_requested/submission_date
                                        (write roles; only before review starts)
    POST  /api/payments/{id}/review/   move a payment through its lifecycle

    Listing/creating payments happens via /api/projects/{id}/payments/ —
    this resource is for direct lookup and review of a single payment.
    """

    serializer_class = PaymentApplicationSerializer
    queryset = PaymentApplication.objects.none()  # overridden by get_queryset
    http_method_names: ClassVar[list[str]] = [
        "get",
        "post",
        "patch",
        "head",
        "options",
    ]

    def get_queryset(self):
        return selectors.payment_queryset_for_user(self.request.user)

    def get_permissions(self):
        if self.action == "review":
            return [IsAuthenticated(), CanReviewPayment()]
        if self.action == "partial_update":
            return [IsAuthenticated(), IsProjectWriterOrReadOnly()]
        return [IsAuthenticated(), IsProjectOrgMember()]

    def partial_update(self, request, *args, **kwargs):
        payment = self.get_object()  # 404 for non-members, 403 for read-only roles
        serializer = self.get_serializer(payment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payment = services.update_payment(
            payment=payment, data=dict(serializer.validated_data)
        )
        return Response(self.get_serializer(payment).data)

    @extend_schema(
        request=PaymentReviewSerializer,
        responses=PaymentApplicationSerializer,
    )
    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        """
        POST /api/payments/{id}/review/ — body: {"decision": "...",
        "amount"?: "...", "notes"?: "..."}

        decision is one of START_REVIEW, RECOMMEND, APPROVE, REJECT,
        RECORD_PAYMENT (apps/projects/services.py
        PaymentReviewDecision). Permission is CanReviewPayment, not
        IsProjectWriterOrReadOnly — a role can create/edit a payment
        without being allowed to review it (separation of duties).
        """
        payment = self.get_object()
        serializer = PaymentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = services.PaymentService.review(
            payment=payment,
            reviewer=request.user,
            **serializer.validated_data,
        )
        return Response(PaymentApplicationSerializer(payment).data)
