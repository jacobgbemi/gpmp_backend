"""
Tests for /api/projects/{id}/evidence/ and /api/evidence/{id}/: upload
validation (extension, declared content-type, and magic-byte signature
must all agree), size limits, the authenticated-only download endpoint,
SITE_INSPECTOR write access, and organization isolation.
"""

import pytest
from rest_framework import status

from apps.inspections.models import ProjectEvidence
from apps.organizations import services as org_services
from apps.organizations.models import Role


def _upload(client, project, file, **overrides):
    payload = {"title": "Crack in slab", "evidence_type": "PHOTO", "file": file} | overrides
    return client.post(f"/api/projects/{project.id}/evidence/", payload, format="multipart")


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEvidenceUploadValidation:
    def test_upload_valid_jpeg(self, user_a, project_a, jpeg_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, jpeg_file)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["original_filename"] == "photo.jpg"
        assert response.data["content_type"] == "image/jpeg"
        assert "download_url" in response.data
        # The raw storage path/URL is never exposed.
        assert "file" not in response.data

    def test_upload_valid_pdf_as_document_evidence(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, pdf_file, evidence_type="DOCUMENT")

        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_valid_mp4_as_video_evidence(self, user_a, project_a, mp4_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, mp4_file, evidence_type="VIDEO")

        assert response.status_code == status.HTTP_201_CREATED

    def test_spoofed_magic_bytes_rejected(self, user_a, project_a, fake_jpeg_file, auth_client):
        """.jpg extension + image/jpeg content-type, but not real JPEG bytes."""
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, fake_jpeg_file)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ProjectEvidence.objects.exists()

    def test_disallowed_extension_rejected(self, user_a, project_a, exe_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, exe_file, evidence_type="OTHER")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ProjectEvidence.objects.exists()

    def test_oversized_file_rejected(self, user_a, project_a, oversized_pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, oversized_pdf_file, evidence_type="DOCUMENT")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_video_file_rejected_when_declared_as_photo(
        self, user_a, project_a, mp4_file, auth_client
    ):
        """evidence_type=PHOTO only accepts the IMAGE kind, not VIDEO."""
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, mp4_file, evidence_type="PHOTO")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_title_rejected(self, user_a, project_a, jpeg_file, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/evidence/",
            {"evidence_type": "PHOTO", "file": jpeg_file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_evidence_records_uploader(self, user_a, project_a, jpeg_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, jpeg_file)

        evidence = ProjectEvidence.objects.get(id=response.data["id"])
        assert evidence.uploaded_by == user_a


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEvidencePermissions:
    def test_viewer_cannot_upload_evidence(
        self, org_a, project_a, jpeg_file, make_user, auth_client
    ):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _upload(client, project_a, jpeg_file)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_site_inspector_can_upload_evidence(
        self, org_a, project_a, jpeg_file, make_user, auth_client
    ):
        inspector = make_user(email="inspector@example.com")
        org_services.add_member(organization=org_a, user=inspector, role=Role.SITE_INSPECTOR)
        client, _ = auth_client(inspector)

        response = _upload(client, project_a, jpeg_file)

        assert response.status_code == status.HTTP_201_CREATED

    def test_foreign_org_user_cannot_upload_evidence(
        self, user_a, project_b, jpeg_file, auth_client
    ):
        client, _ = auth_client(user_a)

        response = _upload(client, project_b, jpeg_file)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Authenticated download
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEvidenceDownload:
    def test_download_requires_authentication(self, user_a, project_a, jpeg_file, auth_client):
        client, _ = auth_client(user_a)
        evidence_id = _upload(client, project_a, jpeg_file).data["id"]

        from rest_framework.test import APIClient

        anon_client = APIClient()
        response = anon_client.get(f"/api/evidence/{evidence_id}/download/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_download_returns_the_uploaded_bytes(
        self, user_a, project_a, jpeg_file, auth_client
    ):
        client, _ = auth_client(user_a)
        evidence_id = _upload(client, project_a, jpeg_file).data["id"]

        response = client.get(f"/api/evidence/{evidence_id}/download/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "image/jpeg"
        content = b"".join(response.streaming_content)
        assert content.startswith(b"\xff\xd8\xff")

    def test_download_sets_content_disposition_with_original_filename(
        self, user_a, project_a, jpeg_file, auth_client
    ):
        client, _ = auth_client(user_a)
        evidence_id = _upload(client, project_a, jpeg_file).data["id"]

        response = client.get(f"/api/evidence/{evidence_id}/download/")

        assert "photo.jpg" in response["Content-Disposition"]

    def test_foreign_org_user_cannot_download(
        self, user_a, project_b, user_b, jpeg_file, auth_client
    ):
        client_b, _ = auth_client(user_b)
        evidence_id = _upload(client_b, project_b, jpeg_file).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/evidence/{evidence_id}/download/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Filtering & linking to an inspection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEvidenceLinkingAndFiltering:
    def test_evidence_can_be_linked_to_an_inspection(
        self, user_a, project_a, jpeg_file, auth_client
    ):
        client, _ = auth_client(user_a)
        insp_id = client.post(
            f"/api/projects/{project_a.id}/inspections/",
            {
                "inspection_type": "QUALITY",
                "inspection_date": "2026-09-01",
                "inspector": str(user_a.id),
            },
            format="json",
        ).data["id"]

        response = _upload(client, project_a, jpeg_file, inspection=insp_id)

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["inspection"]) == insp_id

    def test_evidence_can_stand_alone_without_an_inspection(
        self, user_a, project_a, jpeg_file, auth_client
    ):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, jpeg_file)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["inspection"] is None

    def test_filter_evidence_by_inspection(self, user_a, project_a, make_upload_file, auth_client):
        client, _ = auth_client(user_a)
        insp_id = client.post(
            f"/api/projects/{project_a.id}/inspections/",
            {
                "inspection_type": "QUALITY",
                "inspection_date": "2026-09-01",
                "inspector": str(user_a.id),
            },
            format="json",
        ).data["id"]
        linked = _upload(
            client, project_a, make_upload_file("a.jpg", b"\xff\xd8\xff" + b"0" * 20, "image/jpeg"),
            inspection=insp_id,
        ).data["id"]
        _upload(
            client, project_a, make_upload_file("b.jpg", b"\xff\xd8\xff" + b"0" * 20, "image/jpeg")
        )

        response = client.get(f"/api/projects/{project_a.id}/evidence/?inspection={insp_id}")

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == linked
