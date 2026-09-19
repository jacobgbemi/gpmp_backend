from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login with email + password. Email matching is case-insensitive."""

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().lower()
        return super().validate(attrs)


class MembershipSummarySerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "organization_id",
            "organization_name",
            "organization_slug",
            "role",
        ]
        read_only_fields = fields


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Shape returned by GET /api/auth/me/.

    Deliberately excludes password hash, is_superuser, permissions and other
    sensitive fields.
    """

    memberships = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "memberships"]
        read_only_fields = fields

    def get_memberships(self, user):
        queryset = user.memberships.select_related("organization").order_by(
            "organization__name"
        )
        return MembershipSummarySerializer(queryset, many=True).data