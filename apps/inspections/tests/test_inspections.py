"""
Tests for /api/projects/{id}/inspections/ and /api/inspections/{id}/:
creation, generic status transitions, item CRUD and locking, the
/complete/ workflow and overall_status computation, SITE_INSPECTOR write
access, permissions, and organization isolation.
"""

import pytest
from rest_framework import status

from apps.inspections.models import (
    Inspection,
    InspectionOverallStatus,
    InspectionStatus,
)
from apps.organizations import services as org_services
from apps.organizations.models import Role


def _create_inspection(client, project, inspector_id, **overrides):
    payload = {
        "inspection_type": "QUALITY",
        "inspection_date": "2026-09-01",
        "location": "Level 2",
        "summary": "Routine QA walk",
        "inspector": inspector_id,
    } | overrides
    return client.post(f"/api/projects/{project.id}/inspections/", payload, format="json")


def _add_item(client, inspection_id, **overrides):
    payload = {
        "category": "QUALITY",
        "description": "Tile grouting uneven",
        "status": "OBSERVATION",
    } | overrides
    return client.post(f"/api/inspections/{inspection_id}/items/", payload, format="json")


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInspectionCreation:
    def test_create_inspection(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_inspection(client, project_a, str(user_a.id))

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == InspectionStatus.SCHEDULED
        assert response.data["overall_status"] == InspectionOverallStatus.PENDING

    def test_missing_inspector_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/inspections/",
            {"inspection_type": "QUALITY", "inspection_date": "2026-09-01"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inspector_must_be_organization_member(self, user_a, project_a, user_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_inspection(client, project_a, str(user_b.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_overall_status_cannot_be_set_on_create(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_inspection(client, project_a, str(user_a.id), overall_status="FAIL")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["overall_status"] == InspectionOverallStatus.PENDING

    def test_status_cannot_be_set_on_create(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_inspection(client, project_a, str(user_a.id), status="COMPLETED")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == InspectionStatus.SCHEDULED

    def test_viewer_cannot_create_inspection(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _create_inspection(client, project_a, str(viewer.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_site_inspector_can_create_inspection(self, org_a, project_a, make_user, auth_client):
        """SITE_INSPECTOR is the first role granted real write access — here."""
        inspector = make_user(email="inspector@example.com")
        org_services.add_member(organization=org_a, user=inspector, role=Role.SITE_INSPECTOR)
        client, _ = auth_client(inspector)

        response = _create_inspection(client, project_a, str(inspector.id))

        assert response.status_code == status.HTTP_201_CREATED

    def test_foreign_org_user_cannot_create_inspection(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_inspection(client, project_b, str(user_a.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Generic status transitions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInspectionStatusTransitions:
    def test_scheduled_to_in_progress_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/inspections/{insp_id}/", {"status": "IN_PROGRESS"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_scheduled_to_cancelled_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/inspections/{insp_id}/", {"status": "CANCELLED"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_status_cannot_be_set_to_completed_via_patch(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/inspections/{insp_id}/", {"status": "COMPLETED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        inspection = Inspection.objects.get(id=insp_id)
        assert inspection.status == InspectionStatus.SCHEDULED

    def test_cancelled_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        client.patch(f"/api/inspections/{insp_id}/", {"status": "CANCELLED"}, format="json")

        response = client.patch(
            f"/api/inspections/{insp_id}/", {"status": "IN_PROGRESS"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Inspection items & locking
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInspectionItems:
    def test_add_item(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]

        response = _add_item(client, insp_id)

        assert response.status_code == status.HTTP_201_CREATED

    def test_update_item_before_completion(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        item_id = _add_item(client, insp_id).data["id"]

        response = client.patch(
            f"/api/inspection-items/{item_id}/", {"status": "PASS"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_items_locked_after_inspection_completed(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        item_id = _add_item(client, insp_id, status="PASS").data["id"]
        client.post(f"/api/inspections/{insp_id}/complete/")

        response = client.patch(
            f"/api/inspection-items/{item_id}/", {"status": "FAIL"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_add_item_after_inspection_completed(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        _add_item(client, insp_id, status="PASS")
        client.post(f"/api/inspections/{insp_id}/complete/")

        response = _add_item(client, insp_id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Completion workflow & overall_status computation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInspectionCompletion:
    def test_complete_with_all_pass_items_yields_overall_pass(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        _add_item(client, insp_id, status="PASS")
        _add_item(client, insp_id, status="NOT_APPLICABLE")

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["overall_status"] == InspectionOverallStatus.PASS_
        assert response.data["status"] == InspectionStatus.COMPLETED
        assert response.data["completed_at"] is not None

    def test_complete_with_any_fail_item_yields_overall_fail(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        _add_item(client, insp_id, status="PASS")
        _add_item(client, insp_id, status="FAIL")
        _add_item(client, insp_id, status="OBSERVATION")

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        # FAIL outranks OBSERVATION outranks PASS.
        assert response.data["overall_status"] == InspectionOverallStatus.FAIL

    def test_complete_with_observation_but_no_fail_yields_observation(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        _add_item(client, insp_id, status="PASS")
        _add_item(client, insp_id, status="OBSERVATION")

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        assert response.data["overall_status"] == InspectionOverallStatus.OBSERVATION

    def test_complete_with_no_items_yields_pending(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        assert response.data["overall_status"] == InspectionOverallStatus.PENDING

    def test_cannot_complete_an_already_completed_inspection(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        client.post(f"/api/inspections/{insp_id}/complete/")

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_complete_a_cancelled_inspection(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        insp_id = _create_inspection(client, project_a, str(user_a.id)).data["id"]
        client.patch(f"/api/inspections/{insp_id}/", {"status": "CANCELLED"}, format="json")

        response = client.post(f"/api/inspections/{insp_id}/complete/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInspectionIsolation:
    def test_cannot_retrieve_foreign_org_inspection(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        insp_id = _create_inspection(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/inspections/{insp_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_complete_foreign_org_inspection(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        insp_id = _create_inspection(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.post(f"/api/inspections/{insp_id}/complete/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_inspections(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/inspections/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_access_foreign_org_inspection_item(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        insp_id = _create_inspection(client_b, project_b, str(user_b.id)).data["id"]
        item_id = _add_item(client_b, insp_id).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/inspection-items/{item_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
