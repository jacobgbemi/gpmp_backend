"""
Development settings for GlintPM Private.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# A safe, non-secret fallback so a fresh clone can run immediately.
# Real deployments must always set SECRET_KEY via the environment.
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-local-development-only-do-not-use-in-production",
)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])

# Permissive CORS for local frontend development against the React app.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://127.0.0.1:3000"],
)

# Surface full OpenAPI schema browsing in dev.
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,
    "SERVE_INCLUDE_SCHEMA": True,
}

INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
