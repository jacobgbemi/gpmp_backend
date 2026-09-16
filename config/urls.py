"""
URL configuration for GlintPM Private.

Stage 0 exposes only:
    - /admin/            Django Unfold back-office
    - /api/health/       Health check
    - /api/schema/       Raw OpenAPI schema (drf-spectacular)
    - /api/docs/         Swagger UI
    - /api/redoc/        ReDoc UI
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

    # OpenAPI / Swagger documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]