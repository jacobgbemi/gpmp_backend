from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations import selectors, services
from apps.organizations.permissions import IsOrganizationAdminOrReadOnly
from apps.organizations.serializers import (
    OrganizationMemberSerializer,
    OrganizationSerializer,
)


@extend_schema(tags=["organizations"])
class OrganizationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET   /api/organizations/            organizations the user belongs to
    POST  /api/organizations/            create (creator becomes admin)
    GET   /api/organizations/{id}/
    PATCH /api/organizations/{id}/       admin roles only
    GET   /api/organizations/{id}/members/

    No PUT and no DELETE. Organizations the user does not belong to are not
    in the queryset, so they return 404 — never 403.
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationAdminOrReadOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return selectors.organizations_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = services.create_organization(
            creator=request.user, name=serializer.validated_data["name"]
        )
        # Re-read through the selector so `my_role` is populated.
        organization = self.get_queryset().get(pk=organization.pk)
        return Response(
            self.get_serializer(organization).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(responses=OrganizationMemberSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        organization = self.get_object()  # 404 if not a member
        memberships = selectors.members_of_organization(organization)
        return Response(OrganizationMemberSerializer(memberships, many=True).data)