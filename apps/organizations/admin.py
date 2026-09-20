from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from typing import ClassVar

from apps.organizations.models import Organization, OrganizationMembership


class MembershipInline(TabularInline):
    model = OrganizationMembership
    extra = 0
    autocomplete_fields: ClassVar[list[str]] = ["user"]


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {
        "slug": ("name",),
    }
    inlines: ClassVar[list[type[admin.TabularInline]]] = [MembershipInline]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(ModelAdmin):
    list_display = ("user", "organization", "role", "created_at")
    list_filter = ("role", "organization")
    search_fields = ("user__email", "organization__name")
    autocomplete_fields: ClassVar[list[str]] = ["user", "organization"]
    readonly_fields = ("id", "created_at", "updated_at")
