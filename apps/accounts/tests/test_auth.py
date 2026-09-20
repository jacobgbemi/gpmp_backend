"""
Tests for authentication: /api/auth/token/, /api/auth/token/refresh/,
/api/auth/me/, and the custom User model/manager.
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import User

DEFAULT_PASSWORD = "StrongPass123!"


# ---------------------------------------------------------------------------
# User creation / manager
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUserCreation:
    def test_create_user_hashes_password(self):
        user = User.objects.create_user(email="new@example.com", password="Pass1234!")

        assert user.password != "Pass1234!"
        assert user.check_password("Pass1234!")

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(email="  New@Example.com ", password="Pass1234!")

        assert user.email == "new@example.com"

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="Pass1234!")

    def test_duplicate_email_rejected_case_insensitively(self):
        User.objects.create_user(email="dup@example.com", password="Pass1234!")

        with pytest.raises(IntegrityError):
            User.objects.create_user(email="DUP@example.com", password="Pass1234!")

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="Pass1234!")

        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_new_user_is_active_by_default(self):
        user = User.objects.create_user(email="active@example.com", password="Pass1234!")

        assert user.is_active is True
        assert user.is_staff is False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLogin:
    def test_login_with_correct_credentials_returns_tokens(self, api_client, user_a):
        response = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_is_case_insensitive_on_email(self, api_client, user_a):
        response = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email.upper(), "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_with_wrong_password_fails(self, api_client, user_a):
        response = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": "wrong-password"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unknown_email_fails(self, api_client):
        response = api_client.post(
            "/api/auth/token/",
            {"email": "nobody@example.com", "password": "whatever"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_invalid_email_format_fails(self, api_client):
        response = api_client.post(
            "/api/auth/token/",
            {"email": "not-an-email", "password": "whatever"},
            format="json",
        )

        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_login_response_never_includes_password_hash(self, api_client, user_a):
        response = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert "password" not in response.data

    def test_inactive_user_cannot_login(self, api_client, user_a):
        user_a.is_active = False
        user_a.save(update_fields=["is_active"])

        response = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": DEFAULT_PASSWORD},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_with_valid_token_returns_new_access_token(self, api_client, user_a):
        login = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": DEFAULT_PASSWORD},
            format="json",
        )
        refresh_token = login.data["refresh"]

        response = api_client.post(
            "/api/auth/token/refresh/", {"refresh": refresh_token}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_rotates_and_blacklists_old_token(self, api_client, user_a):
        login = api_client.post(
            "/api/auth/token/",
            {"email": user_a.email, "password": DEFAULT_PASSWORD},
            format="json",
        )
        old_refresh = login.data["refresh"]

        first_use = api_client.post(
            "/api/auth/token/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert first_use.status_code == status.HTTP_200_OK

        second_use = api_client.post(
            "/api/auth/token/refresh/", {"refresh": old_refresh}, format="json"
        )
        assert second_use.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_malformed_token_fails(self, api_client):
        response = api_client.post(
            "/api/auth/token/refresh/", {"refresh": "not-a-real-token"}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_with_missing_token_fails(self, api_client):
        response = api_client.post("/api/auth/token/refresh/", {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_refresh_with_expired_token_fails(self, api_client, user_a):
        expired_refresh = RefreshToken.for_user(user_a)
        expired_refresh.set_exp(lifetime=timedelta(seconds=-1))

        response = api_client.post(
            "/api/auth/token/refresh/", {"refresh": str(expired_refresh)}, format="json"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCurrentUser:
    def test_me_returns_current_user_profile(self, user_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user_a.email
        assert response.data["id"] == str(user_a.id)

    def test_me_never_exposes_password_or_privileged_fields(self, user_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get("/api/auth/me/")

        assert "password" not in response.data
        assert "is_superuser" not in response.data
        assert "is_staff" not in response.data

    def test_me_includes_organization_memberships(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get("/api/auth/me/")

        assert len(response.data["memberships"]) == 1
        assert response.data["memberships"][0]["organization_id"] == str(org_a.id)
        assert response.data["memberships"][0]["role"] == "ORGANIZATION_ADMIN"

    def test_me_without_token_is_unauthorized(self, api_client):
        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_malformed_token_is_unauthorized(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_expired_token_is_unauthorized(self, api_client, user_a):
        token = AccessToken.for_user(user_a)
        token.set_exp(lifetime=timedelta(seconds=-1))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_malformed_auth_header_is_unauthorized(self, api_client, user_a):
        token = AccessToken.for_user(user_a)
        # Missing the "Bearer " prefix entirely.
        api_client.credentials(HTTP_AUTHORIZATION=str(token))

        response = api_client.get("/api/auth/me/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_timestamp_sanity(self, user_a, auth_client):
        """The token issued just now should not be treated as expired."""
        _client, data = auth_client(user_a)
        access = AccessToken(data["access"])

        assert access["exp"] > timezone.now().timestamp()