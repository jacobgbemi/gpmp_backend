"""
Foundation tests for the backend project as a whole.

These verify the project boots correctly and that the security foundation
(custom user, JWT, Unfold registrations) plus the expected set of business
apps are wired in — not business logic itself, which is covered in each
app's own tests/ package.
"""

import pytest
from django.apps import apps
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient


class TestDjangoBootsCorrectly:
    def test_settings_module_is_loaded(self):
        assert settings.configured

    def test_debug_is_boolean(self):
        assert isinstance(settings.DEBUG, bool)

    def test_secret_key_is_set(self):
        assert settings.SECRET_KEY

    def test_installed_apps_includes_unfold_before_admin(self):
        installed = settings.INSTALLED_APPS
        assert "unfold" in installed
        assert "django.contrib.admin" in installed
        assert installed.index("unfold") < installed.index("django.contrib.admin")

    def test_custom_user_model_is_configured(self):
        assert settings.AUTH_USER_MODEL == "accounts.User"

    def test_no_premature_business_domain_apps(self):
        """
        Stage 3 adds variations + risks (which also covers issues — see
        apps/risks/models.py). Inspections, documents, reports, and
        notifications are still out of scope until their own stages.
        """
        forbidden_labels = {
            "inspections",
            "documents",
            "reports",
            "contractors",
            "notifications",
            "audit",
        }
        installed_labels = {cfg.label for cfg in apps.get_app_configs()}
        assert installed_labels.isdisjoint(forbidden_labels)

    def test_expected_stage3_apps_are_installed(self):
        installed_labels = {cfg.label for cfg in apps.get_app_configs()}
        assert {
            "core",
            "accounts",
            "organizations",
            "projects",
            "variations",
            "risks",
        }.issubset(installed_labels)


@pytest.mark.django_db
class TestDatabaseConnection:
    def test_database_is_reachable(self):
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)

    def test_custom_user_table_exists(self):
        from apps.accounts.models import User

        assert User.objects.count() >= 0  # table exists and is queryable


@pytest.mark.django_db
class TestAdminAndUnfold:
    def test_admin_login_page_loads(self, client):
        response = client.get("/admin/login/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_index_redirects_anonymous_to_login(self, client):
        response = client.get("/admin/")
        assert response.status_code in (
            status.HTTP_302_FOUND,
            status.HTTP_301_MOVED_PERMANENTLY,
        )

    def test_unfold_app_is_installed(self):
        assert apps.is_installed("unfold")

    def test_unfold_config_is_present(self):
        assert hasattr(settings, "UNFOLD")
        assert settings.UNFOLD["SITE_TITLE"] == "GlintPM Private"

    def test_user_model_is_registered_in_admin(self):
        from django.contrib import admin

        from apps.accounts.models import User

        assert admin.site.is_registered(User)

    def test_organization_model_is_registered_in_admin(self):
        from django.contrib import admin

        from apps.organizations.models import Organization, OrganizationMembership

        assert admin.site.is_registered(Organization)
        assert admin.site.is_registered(OrganizationMembership)

    def test_project_models_are_registered_in_admin(self):
        from django.contrib import admin

        from apps.projects.models import (
            BudgetItem,
            PaymentApplication,
            ProgressUpdate,
            Project,
            ProjectBudget,
        )

        assert admin.site.is_registered(Project)
        assert admin.site.is_registered(ProjectBudget)
        assert admin.site.is_registered(BudgetItem)
        assert admin.site.is_registered(ProgressUpdate)
        assert admin.site.is_registered(PaymentApplication)

    def test_variation_model_is_registered_in_admin(self):
        from django.contrib import admin

        from apps.variations.models import Variation

        assert admin.site.is_registered(Variation)

    def test_risk_and_issue_models_are_registered_in_admin(self):
        from django.contrib import admin

        from apps.risks.models import Issue, Risk

        assert admin.site.is_registered(Risk)
        assert admin.site.is_registered(Issue)


@pytest.mark.django_db
class TestOpenAPIDocumentation:
    def test_schema_endpoint_loads(self):
        client = APIClient()
        response = client.get("/api/schema/")
        assert response.status_code == status.HTTP_200_OK

    def test_swagger_ui_loads(self):
        client = APIClient()
        response = client.get("/api/docs/")
        assert response.status_code == status.HTTP_200_OK

    def test_redoc_loads(self):
        client = APIClient()
        response = client.get("/api/redoc/")
        assert response.status_code == status.HTTP_200_OK


class TestJWTConfiguration:
    def test_access_and_refresh_token_lifetimes_are_set(self):
        simple_jwt = settings.SIMPLE_JWT
        assert simple_jwt["ACCESS_TOKEN_LIFETIME"].total_seconds() > 0
        assert simple_jwt["REFRESH_TOKEN_LIFETIME"].total_seconds() > 0

    def test_refresh_token_rotation_and_blacklist_enabled(self):
        simple_jwt = settings.SIMPLE_JWT
        assert simple_jwt["ROTATE_REFRESH_TOKENS"] is True
        assert simple_jwt["BLACKLIST_AFTER_ROTATION"] is True

    def test_token_blacklist_app_installed(self):
        assert apps.is_installed("rest_framework_simplejwt.token_blacklist")
