"""
Tests for /api/projects/{id}/documents/ and /api/documents/{id}/: upload
validation, metadata-only PATCH (never the file), versioning (is_latest
flipping, document_group sharing, duplicate-version rejection), the
authenticated download endpoint, and organization isolation.
"""

import pytest
from django.db import IntegrityError, transaction
from rest_framework import status

from apps.documents.models import Document
from apps.organizations import services as org_services
from apps.organizations.models import Role


def _upload(client, project, file, **overrides):
    payload = {"name": "Main Contract", "document_type": "CONTRACT", "file": file} | overrides
    return client.post(f"/api/projects/{project.id}/documents/", payload, format="multipart")


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentUploadValidation:
    def test_upload_valid_pdf(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, pdf_file)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["version"] == 1
        assert response.data["is_latest"] is True
        assert "file" not in response.data

    def test_disallowed_extension_rejected(self, user_a, project_a, exe_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, exe_file)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Document.objects.exists()

    def test_spoofed_pdf_rejected(self, user_a, project_a, fake_jpeg_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, fake_jpeg_file, document_type="OTHER")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_oversized_document_rejected(self, user_a, project_a, oversized_pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, oversized_pdf_file)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_drawing_accepts_image_file(self, user_a, project_a, jpeg_file, auth_client):
        """DRAWING is the one document_type that also accepts images."""
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, jpeg_file, document_type="DRAWING", name="Site plan")

        assert response.status_code == status.HTTP_201_CREATED

    def test_contract_rejects_image_file(self, user_a, project_a, jpeg_file, auth_client):
        """Only DRAWING gets the image exception — CONTRACT does not."""
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, jpeg_file, document_type="CONTRACT")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_document_records_uploader(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_a, pdf_file)

        document = Document.objects.get(id=response.data["id"])
        assert document.uploaded_by == user_a


# ---------------------------------------------------------------------------
# Metadata update (never the file)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentMetadataUpdate:
    def test_update_name_and_status(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]

        response = client.patch(
            f"/api/documents/{doc_id}/",
            {"name": "Signed Main Contract", "status": "ACTIVE"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Signed Main Contract"

    def test_patch_cannot_replace_the_file(self, user_a, project_a, pdf_file, jpeg_file, auth_client):
        """The file field isn't even present on the update serializer."""
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]

        response = client.patch(
            f"/api/documents/{doc_id}/",
            {"name": "Try to sneak a file in", "file": jpeg_file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        document = Document.objects.get(id=doc_id)
        assert document.file_extension == "pdf"  # unchanged

    def test_version_is_not_patchable(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]

        response = client.patch(
            f"/api/documents/{doc_id}/", {"version": 99}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        document = Document.objects.get(id=doc_id)
        assert document.version == 1


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentVersioning:
    def test_create_new_version(self, user_a, project_a, pdf_file, make_upload_file, auth_client):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2 content\n%%EOF", "application/pdf")

        response = client.post(
            f"/api/documents/{doc_id}/versions/",
            {"file": v2_file, "change_notes": "Updated clause 5.2"},
            format="multipart",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["version"] == 2
        assert response.data["is_latest"] is True
        assert response.data["change_notes"] == "Updated clause 5.2"

    def test_new_version_shares_document_group(
        self, user_a, project_a, pdf_file, make_upload_file, auth_client
    ):
        client, _ = auth_client(user_a)
        v1 = _upload(client, project_a, pdf_file).data
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")

        v2 = client.post(
            f"/api/documents/{v1['id']}/versions/", {"file": v2_file}, format="multipart"
        ).data

        assert v2["document_group"] == v1["document_group"]

    def test_previous_version_is_latest_flips_to_false(
        self, user_a, project_a, pdf_file, make_upload_file, auth_client
    ):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")
        client.post(f"/api/documents/{doc_id}/versions/", {"file": v2_file}, format="multipart")

        response = client.get(f"/api/documents/{doc_id}/")

        assert response.data["is_latest"] is False

    def test_new_version_inherits_metadata_from_previous(
        self, user_a, project_a, pdf_file, make_upload_file, auth_client
    ):
        client, _ = auth_client(user_a)
        doc_id = _upload(
            client, project_a, pdf_file, name="Main Contract", document_type="CONTRACT"
        ).data["id"]
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")

        v2 = client.post(
            f"/api/documents/{doc_id}/versions/", {"file": v2_file}, format="multipart"
        ).data

        assert v2["name"] == "Main Contract"
        assert v2["document_type"] == "CONTRACT"

    def test_list_versions_returns_all_in_descending_order(
        self, user_a, project_a, pdf_file, make_upload_file, auth_client
    ):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")
        client.post(f"/api/documents/{doc_id}/versions/", {"file": v2_file}, format="multipart")

        response = client.get(f"/api/documents/{doc_id}/versions/")

        versions = [row["version"] for row in response.data]
        assert versions == [2, 1]

    def test_project_document_list_shows_only_latest_version(
        self, user_a, project_a, pdf_file, make_upload_file, auth_client
    ):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")
        client.post(f"/api/documents/{doc_id}/versions/", {"file": v2_file}, format="multipart")

        response = client.get(f"/api/projects/{project_a.id}/documents/")

        assert response.data["count"] == 1
        assert response.data["results"][0]["version"] == 2

    def test_duplicate_version_number_rejected_at_database_level(
        self, user_a, project_a, pdf_file, auth_client
    ):
        """
        The API can never produce a duplicate (version is always
        server-computed as current-max + 1) — this proves the database
        constraint itself is the backstop, independent of the service.
        """
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]
        document = Document.objects.get(id=doc_id)

        with pytest.raises(IntegrityError), transaction.atomic():
            Document.objects.create(
                project=document.project,
                name="Duplicate",
                document_type="CONTRACT",
                file=document.file,
                original_filename="dup.pdf",
                file_extension="pdf",
                content_type="application/pdf",
                file_size=10,
                document_group=document.document_group,
                version=1,  # same group, same version as the existing row
                uploaded_by=user_a,
            )

    def test_viewer_cannot_create_new_version(
        self, user_a, org_a, project_a, pdf_file, make_user, make_upload_file, auth_client
    ):
        admin_client, _ = auth_client(user_a)
        doc_id = _upload(admin_client, project_a, pdf_file).data["id"]
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        viewer_client, _ = auth_client(viewer)
        v2_file = make_upload_file("v2.pdf", b"%PDF-1.4\nv2\n%%EOF", "application/pdf")

        response = viewer_client.post(
            f"/api/documents/{doc_id}/versions/", {"file": v2_file}, format="multipart"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Authenticated download
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentDownload:
    def test_download_requires_authentication(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]

        from rest_framework.test import APIClient

        anon_client = APIClient()
        response = anon_client.get(f"/api/documents/{doc_id}/download/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_download_returns_the_uploaded_bytes(self, user_a, project_a, pdf_file, auth_client):
        client, _ = auth_client(user_a)
        doc_id = _upload(client, project_a, pdf_file).data["id"]

        response = client.get(f"/api/documents/{doc_id}/download/")

        assert response.status_code == status.HTTP_200_OK
        content = b"".join(response.streaming_content)
        assert content.startswith(b"%PDF-")

    def test_foreign_org_user_cannot_download(
        self, user_a, project_b, user_b, pdf_file, auth_client
    ):
        client_b, _ = auth_client(user_b)
        doc_id = _upload(client_b, project_b, pdf_file).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/documents/{doc_id}/download/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDocumentIsolation:
    def test_cannot_retrieve_foreign_org_document(
        self, user_a, project_b, user_b, pdf_file, auth_client
    ):
        client_b, _ = auth_client(user_b)
        doc_id = _upload(client_b, project_b, pdf_file).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/documents/{doc_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_documents(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/documents/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_foreign_org_user_cannot_create_document(self, user_a, project_b, pdf_file, auth_client):
        client, _ = auth_client(user_a)

        response = _upload(client, project_b, pdf_file)

        assert response.status_code == status.HTTP_404_NOT_FOUND
