from rest_framework import serializers
from typing import ClassVar

from apps.organizations.models import Organization, OrganizationMembership


class OrganizationSerializer(serializers.ModelSerializer):
    my_role = serializers.CharField(read_only=True)

    class Meta:
        model = Organization
        fields: ClassVar[list[str]] = [
            "id",
            "name",
            "slug",
            "my_role",
            "created_at",
            "updated_at",
        ]

        read_only_fields: ClassVar[list[str]] = [
            "id",
            "slug",
            "my_role",
            "created_at",
            "updated_at",
        ]


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user_id", "email", "first_name", "last_name", "role"]
        read_only_fields = fields
