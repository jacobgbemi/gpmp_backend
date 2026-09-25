"""
URL configuration for GlintPM Private.

    - /admin/                Django Unfold back-office
    - /api/health/           Health check
    - /api/auth/             Authentication (login, refresh, /me/)
    - /api/organizations/    Organizations and membership
    - /api/projects/         Projects, budgets, progress, payments, dashboard,
                             plus nested variations/risks/issues list+create
    - /api/payments/         Direct payment lookup + review
    - /api/variations/       Direct variation lookup, update, approve
    - /api/risks/            Direct risk lookup + update
    - /api/issues/           Direct issue lookup + update
    - /api/schema/           Raw OpenAPI schema (drf-spectacular)
    - /api/docs/             Swagger UI
    - /api/redoc/            ReDoc UI
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.organizations.urls")),
    path("api/", include("apps.projects.urls")),
    path("api/", include("apps.variations.urls")),
    path("api/", include("apps.risks.urls")),
    # OpenAPI / Swagger documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
