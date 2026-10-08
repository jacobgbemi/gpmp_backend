"""
Tests for /api/projects/{id}/folders/ and /api/folders/{id}/: creation,
nested subfolders, duplicate-name rejection (per location), cross-project
parent validation, permissions, and organization isolation.
"""

import pytest
from rest_framework import status

from apps.documents.models import DocumentFolder
from apps.organizations import services as org_services
from apps.organizations.models import Role


def _create_folder(client, project, **overrides):
    payload = {"name": "Contracts"} | overrides
    return client.post(f"/api/projects/{project.id}/folders/", payload, format="json")


@pytest.mark.django_db
class TestFolderCreation:
    def test_create_folder(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_folder(client, project_a)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["parent"] is None

    def test_create_nested_subfolder(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        parent_id = _create_folder(client, project_a).data["id"]

        response = _create_folder(client, project_a, name="Signed Copies", parent=parent_id)

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["parent"]) == parent_id

    def test_duplicate_name_at_same_location_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_folder(client, project_a, name="Contracts")

        response = _create_folder(client, project_a, name="Contracts")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_name_allowed_in_different_parent_folders(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        parent_1 = _create_folder(client, project_a, name="Phase 1").data["id"]
        parent_2 = _create_folder(client, project_a, name="Phase 2").data["id"]

        first = _create_folder(client, project_a, name="Drawings", parent=parent_1)
        second = _create_folder(client, project_a, name="Drawings", parent=parent_2)

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED

    def test_same_name_allowed_in_different_projects(
        self, user_a, project_a, make_project, org_a, auth_client
    ):
        other_project = make_project(org_a, project_code="OTHER-FOLDER")
        client, _ = auth_client(user_a)

        first = _create_folder(client, project_a, name="Contracts")
        second = _create_folder(client, other_project, name="Contracts")

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED

    def test_viewer_cannot_create_folder(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _create_folder(client, project_a)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_create_folder(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_folder(client, project_b)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestFolderUpdate:
    def test_rename_folder(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        folder_id = _create_folder(client, project_a).data["id"]

        response = client.patch(
            f"/api/folders/{folder_id}/", {"name": "Legal Contracts"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Legal Contracts"


@pytest.mark.django_db
class TestFolderIsolation:
    def test_cannot_retrieve_foreign_org_folder(self, user_a, project_b, user_b, auth_client):
        client_b, _ = auth_client(user_b)
        folder_id = _create_folder(client_b, project_b).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/folders/{folder_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_folders(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/folders/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_document_cannot_reference_a_foreign_project_folder(
        self, user_a, project_a, project_b, user_b, pdf_file, auth_client
    ):
        """
        Defense in depth: even though the folder dropdown is already
        restricted to the project's own folders, the service independently
        validates folder.project == document.project.
        """
        client_b, _ = auth_client(user_b)
        foreign_folder_id = _create_folder(client_b, project_b).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.post(
            f"/api/projects/{project_a.id}/documents/",
            {
                "name": "X",
                "document_type": "CONTRACT",
                "folder": foreign_folder_id,
                "file": pdf_file,
            },
            format="multipart",
        )

        # The foreign folder isn't even a valid choice in project_a's
        # restricted queryset, so this is a 400 (invalid choice), not a
        # 403/404 — the field's queryset never included it to begin with.
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not DocumentFolder.objects.filter(id=foreign_folder_id, project=project_a).exists()
