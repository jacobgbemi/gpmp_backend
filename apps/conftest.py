"""
Shared pytest fixtures for tests under apps/.

Lives here (rather than under a single app's tests/) so both
apps/accounts/tests/ and apps/organizations/tests/ can use the same
fixtures — pytest resolves conftest.py by walking up from the test file to
the rootdir.
"""

import itertools
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects.models import Project, ProjectBudget, ProjectType

DEFAULT_PASSWORD = "StrongPass123!"
_project_code_counter = itertools.count(1)


@pytest.fixture(autouse=True)
def _isolated_media_root(settings, tmp_path):
    """
    Every test gets its own throwaway MEDIA_ROOT, so uploads made during a
    test run never land in (or get mixed up with) a developer's real
    media/ directory, and nothing needs manual cleanup afterwards.
    """
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(email="user@example.com", password=DEFAULT_PASSWORD, **kwargs):
        return User.objects.create_user(email=email, password=password, **kwargs)

    return _make_user


@pytest.fixture
def user_a(make_user):
    return make_user(email="a@example.com", first_name="Alice", last_name="A")


@pytest.fixture
def user_b(make_user):
    return make_user(email="b@example.com", first_name="Bob", last_name="B")


@pytest.fixture
def org_a(db, user_a):
    organization = Organization.objects.create(name="Org A", slug="org-a")
    OrganizationMembership.objects.create(
        user=user_a, organization=organization, role=Role.ORGANIZATION_ADMIN
    )
    return organization


@pytest.fixture
def org_b(db, user_b):
    organization = Organization.objects.create(name="Org B", slug="org-b")
    OrganizationMembership.objects.create(
        user=user_b, organization=organization, role=Role.ORGANIZATION_ADMIN
    )
    return organization


@pytest.fixture
def auth_client():
    """
    Factory fixture: auth_client(user) -> (APIClient, token_pair_dict)

    The client carries a valid Bearer access token obtained through the
    real /api/auth/token/ endpoint (not a shortcut), so tests exercise the
    actual login path.
    """

    def _auth_client(user, password=DEFAULT_PASSWORD):
        client = APIClient()
        response = client.post(
            "/api/auth/token/",
            {"email": user.email, "password": password},
            format="json",
        )
        assert response.status_code == 200, response.data
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client, response.data

    return _auth_client


@pytest.fixture
def make_project(db):
    def _make_project(organization, **kwargs):
        kwargs.setdefault("name", "Lekki Residence")
        kwargs.setdefault("project_code", f"PRJ-{next(_project_code_counter):04d}")
        kwargs.setdefault("project_type", ProjectType.RESIDENTIAL)
        kwargs.setdefault("contract_value", Decimal("500000000.00"))
        project = Project.objects.create(organization=organization, **kwargs)
        ProjectBudget.objects.get_or_create(project=project)
        return project

    return _make_project


@pytest.fixture
def project_a(make_project, org_a):
    return make_project(org_a)


@pytest.fixture
def project_b(make_project, org_b):
    return make_project(org_b)


# ---------------------------------------------------------------------------
# File-upload fixtures (Stage 4) — real, valid magic bytes for each kind,
# so tests exercise the actual signature check in common.file_validation
# rather than a shortcut around it.
# ---------------------------------------------------------------------------

_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 50
_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
_PDF_BYTES = b"%PDF-1.4\n%fake pdf content for testing\n%%EOF"
_MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 50


@pytest.fixture
def make_upload_file():
    def _make(name, content, content_type):
        return SimpleUploadedFile(name, content, content_type=content_type)

    return _make


@pytest.fixture
def jpeg_file(make_upload_file):
    return make_upload_file("photo.jpg", _JPEG_BYTES, "image/jpeg")


@pytest.fixture
def png_file(make_upload_file):
    return make_upload_file("photo.png", _PNG_BYTES, "image/png")


@pytest.fixture
def pdf_file(make_upload_file):
    return make_upload_file("document.pdf", _PDF_BYTES, "application/pdf")


@pytest.fixture
def mp4_file(make_upload_file):
    return make_upload_file("clip.mp4", _MP4_BYTES, "video/mp4")


@pytest.fixture
def fake_jpeg_file(make_upload_file):
    """.jpg extension + image content-type, but NOT actually JPEG bytes."""
    return make_upload_file("fake.jpg", b"this is not an image, just text", "image/jpeg")


@pytest.fixture
def exe_file(make_upload_file):
    return make_upload_file("virus.exe", b"MZ fake executable content", "application/octet-stream")


@pytest.fixture
def oversized_pdf_file(make_upload_file):
    # Over both the document (20MB) and evidence (25MB) defaults — content
    # doesn't need to be a real PDF since the size check runs before the
    # signature check.
    return make_upload_file("huge.pdf", b"%PDF-" + b"0" * (30 * 1024 * 1024), "application/pdf")
