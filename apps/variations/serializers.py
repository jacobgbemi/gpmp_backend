from typing import ClassVar

from rest_framework import serializers

from apps.variations.models import Variation


class VariationSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    approved_by_email = serializers.EmailField(
        source="approved_by.email", read_only=True, default=None
    )
    requested_date = serializers.DateField(required=False)

    class Meta:
        model = Variation
        fields: ClassVar[list[str]] = [
            "id",
            "variation_number",
            "title",
            "description",
            "reason",
            "category",
            "requested_amount",
            "estimated_amount",
            "approved_amount",
            "status",
            "requested_date",
            "approved_date",
            "notes",
            "created_by_email",
            "approved_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields: ClassVar[list[str]] = [
            "id",
            "approved_amount",
            "approved_date",
            "created_by_email",
            "approved_by_email",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            # Creating: status always starts at PROPOSED — never
            # client-settable, blocking mass assignment of an initial
            # status such as APPROVED.
            self.fields["status"].read_only = True


class VariationApproveSerializer(serializers.Serializer):
    approved_amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
