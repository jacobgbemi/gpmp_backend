"""
Tests for /api/projects/: CRUD, organization isolation/IDOR, role
permissions, status-transition validation, date validation, duplicate
project codes, and mass-assignment protection.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.projects.models import Project, ProjectStatus

# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectCRUD:
    def test_create_project(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "Lekki Residence",
                "project_code": "LEK-001",
                "project_type": "RESIDENTIAL",
                "contract_value": "500000000.00",
                "currency": "NGN",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == ProjectStatus.PLANNING
        assert response.data["contract_value"] == "500000000.00"

    def test_list_returns_only_own_organization_projects(
        self, user_a, project_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get("/api/projects/")

        ids = {p["id"] for p in response.data["results"]}
        assert ids == {str(project_a.id)}

    def test_retrieve_project(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_a.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(project_a.id)

    def test_patch_updates_allowed_fields(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"name": "Renamed Project"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Renamed Project"

    def test_delete_project_with_no_financial_history_succeeds(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.delete(f"/api/projects/{project_a.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(id=project_a.id).exists()

    def test_delete_blocked_once_a_payment_is_approved(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        payment_id = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]
        client.post(
            f"/api/payments/{payment_id}/review/",
            {"decision": "START_REVIEW"},
            format="json",
        )
        client.post(
            f"/api/payments/{payment_id}/review/",
            {"decision": "RECOMMEND", "amount": "1000.00"},
            format="json",
        )
        client.post(
            f"/api/payments/{payment_id}/review/",
            {"decision": "APPROVE", "amount": "1000.00"},
            format="json",
        )

        response = client.delete(f"/api/projects/{project_a.id}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Project.objects.filter(id=project_a.id).exists()

    def test_delete_allowed_when_payments_only_submitted_or_rejected(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        )
        rejected_id = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "2000.00"},
            format="json",
        ).data["id"]
        client.post(
            f"/api/payments/{rejected_id}/review/",
            {"decision": "REJECT", "notes": "duplicate"},
            format="json",
        )

        response = client.delete(f"/api/projects/{project_a.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_create_requires_authentication(self, api_client, org_a):
        response = api_client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectOrganizationIsolation:
    def test_user_cannot_retrieve_foreign_org_project(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_patch_foreign_org_project(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)
        original_name = project_b.name

        response = client.patch(
            f"/api/projects/{project_b.id}/", {"name": "Hacked"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        project_b.refresh_from_db()
        assert project_b.name == original_name

    def test_user_cannot_delete_foreign_org_project(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.delete(f"/api/projects/{project_b.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Project.objects.filter(id=project_b.id).exists()

    def test_cannot_create_project_in_foreign_organization(
        self, user_a, org_b, auth_client
    ):
        """
        user_a is not a member of org_b at all, so org_b is not even a
        valid choice — this is a 400 (invalid choice), not a 403/404, since
        the field's queryset never included org_b to begin with.
        """
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_b.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_404_for_foreign_project_matches_404_for_random_uuid(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        foreign = client.get(f"/api/projects/{project_b.id}/")
        random_uuid = client.get("/api/projects/00000000-0000-0000-0000-000000000000/")

        assert foreign.status_code == random_uuid.status_code == 404
        assert foreign.data == random_uuid.data

    def test_project_id_cannot_be_guessed_across_organizations_by_changing_uuid(
        self, user_a, org_a, project_a, project_b, auth_client
    ):
        """A member of Org A must never reach Org B's project via UUID alone."""
        client, _ = auth_client(user_a)

        own = client.get(f"/api/projects/{project_a.id}/")
        foreign = client.get(f"/api/projects/{project_b.id}/")

        assert own.status_code == 200
        assert foreign.status_code == 404


# ---------------------------------------------------------------------------
# Role permissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectRolePermissions:
    def test_viewer_cannot_create_project(self, org_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_can_read_project(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer2@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.get(f"/api/projects/{project_a.id}/")

        assert response.status_code == status.HTTP_200_OK

    def test_viewer_cannot_patch_project(
        self, org_a, project_a, make_user, auth_client
    ):
        viewer = make_user(email="viewer3@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"name": "Renamed"}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_project_manager_can_create_project(self, org_a, make_user, auth_client):
        pm = make_user(email="pm@example.com")
        org_services.add_member(organization=org_a, user=pm, role=Role.PROJECT_MANAGER)
        client, _ = auth_client(pm)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_project_controls_can_create_project(self, org_a, make_user, auth_client):
        controls = make_user(email="controls@example.com")
        org_services.add_member(
            organization=org_a, user=controls, role=Role.PROJECT_CONTROLS
        )
        client, _ = auth_client(controls)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_consultant_cannot_create_project(self, org_a, make_user, auth_client):
        consultant = make_user(email="consultant@example.com")
        org_services.add_member(
            organization=org_a, user=consultant, role=Role.CONSULTANT
        )
        client, _ = auth_client(consultant)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Mass assignment
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectMassAssignment:
    def test_status_cannot_be_set_directly_on_create(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
                "status": "COMPLETED",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == ProjectStatus.PLANNING

    def test_organization_is_immutable_after_creation(
        self, user_a, org_a, org_b, project_a, auth_client
    ):
        """
        Even though user_a only belongs to org_a (so org_b wouldn't even be
        a valid queryset choice), the field is explicitly read-only on
        update as defense in depth.
        """
        client, _ = auth_client(user_a)

        response = client.patch(
            f"/api/projects/{project_a.id}/",
            {"organization": str(org_a.id), "name": "Still same org"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        project_a.refresh_from_db()
        assert project_a.organization_id == org_a.id


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectDateValidation:
    def test_planned_end_before_planned_start_rejected(
        self, user_a, org_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
                "planned_start_date": "2026-06-01",
                "planned_end_date": "2026-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_actual_end_before_actual_start_rejected(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
                "actual_start_date": "2026-06-01",
                "actual_end_date": "2026-01-01",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_date_ranges_accepted(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "1000.00",
                "planned_start_date": "2026-01-01",
                "planned_end_date": "2026-12-31",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED


# ---------------------------------------------------------------------------
# Status transition validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectStatusTransitions:
    def test_planning_to_active_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "ACTIVE"

    def test_planning_to_completed_is_invalid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "COMPLETED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_completed_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )
        client.patch(
            f"/api/projects/{project_a.id}/", {"status": "COMPLETED"}, format="json"
        )

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancelled_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.patch(
            f"/api/projects/{project_a.id}/", {"status": "CANCELLED"}, format="json"
        )

        response = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_active_can_go_on_hold_and_back(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )

        on_hold = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ON_HOLD"}, format="json"
        )
        back_active = client.patch(
            f"/api/projects/{project_a.id}/", {"status": "ACTIVE"}, format="json"
        )

        assert on_hold.status_code == 200
        assert back_active.status_code == 200


# ---------------------------------------------------------------------------
# Duplicate project codes / money precision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectValidation:
    def test_duplicate_project_code_within_same_organization_rejected(
        self, user_a, org_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "Another project",
                "project_code": project_a.project_code,
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_project_code_allowed_in_different_organizations(
        self, user_a, org_a, user_b, org_b, auth_client
    ):
        client_a, _ = auth_client(user_a)
        client_b, _ = auth_client(user_b)

        first = client_a.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "SHARED-001",
                "contract_value": "1000.00",
            },
            format="json",
        )
        second = client_b.post(
            "/api/projects/",
            {
                "organization": str(org_b.id),
                "name": "Y",
                "project_code": "SHARED-001",
                "contract_value": "1000.00",
            },
            format="json",
        )

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED

    def test_negative_contract_value_rejected(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "-1000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_contract_value_preserves_decimal_precision(
        self, user_a, org_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/projects/",
            {
                "organization": str(org_a.id),
                "name": "X",
                "project_code": "X-1",
                "contract_value": "500000000.33",
            },
            format="json",
        )

        assert response.data["contract_value"] == "500000000.33"
        project = Project.objects.get(id=response.data["id"])
        assert project.contract_value == Decimal("500000000.33")
