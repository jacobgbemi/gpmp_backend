"""
Tests for /api/projects/{id}/issues/ and /api/issues/{id}/: creation,
status transitions, the resolution-required-for-RESOLVED rule, owner
validation, permissions, filtering, and organization isolation.
"""

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role


def _create_issue(client, project, owner_id, **overrides):
    payload = {
        "title": "Cracked slab found",
        "severity": "HIGH",
        "owner": owner_id,
    } | overrides
    return client.post(f"/api/projects/{project.id}/issues/", payload, format="json")


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIssueCreation:
    def test_create_issue(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_issue(client, project_a, str(user_a.id))

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "OPEN"
        assert response.data["resolution"] == ""

    def test_missing_owner_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/issues/",
            {"title": "X", "severity": "LOW"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_owner_must_be_organization_member(
        self, user_a, project_a, user_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = _create_issue(client, project_a, str(user_b.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_viewer_cannot_create_issue(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _create_issue(client, project_a, str(viewer.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_create_issue(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_issue(client, project_b, str(user_a.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Status transitions & resolution requirement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIssueStatusTransitions:
    def test_open_to_in_progress_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/issues/{issue_id}/", {"status": "IN_PROGRESS"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_resolve_without_resolution_text_rejected(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/issues/{issue_id}/", {"status": "RESOLVED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resolve_with_resolution_text_succeeds(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/issues/{issue_id}/",
            {"status": "RESOLVED", "resolution": "Slab repaired and re-inspected"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "RESOLVED"

    def test_resolved_can_be_reopened_to_in_progress(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]
        client.patch(
            f"/api/issues/{issue_id}/",
            {"status": "RESOLVED", "resolution": "Fixed"},
            format="json",
        )

        response = client.patch(
            f"/api/issues/{issue_id}/", {"status": "IN_PROGRESS"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_closed_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]
        client.patch(f"/api/issues/{issue_id}/", {"status": "CLOSED"}, format="json")

        response = client.patch(
            f"/api/issues/{issue_id}/", {"status": "OPEN"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resolution_already_present_satisfies_resolve_requirement(
        self, user_a, project_a, auth_client
    ):
        """
        If a resolution was already recorded in an earlier PATCH, a later
        PATCH that only sets status=RESOLVED (without repeating the text)
        still succeeds — the requirement is "a resolution exists", not
        "resolution was supplied in this exact request".
        """
        client, _ = auth_client(user_a)
        issue_id = _create_issue(client, project_a, str(user_a.id)).data["id"]
        client.patch(
            f"/api/issues/{issue_id}/",
            {"status": "IN_PROGRESS", "resolution": "Working on it, root cause found"},
            format="json",
        )

        response = client.patch(
            f"/api/issues/{issue_id}/", {"status": "RESOLVED"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIssueFiltering:
    def test_filter_by_severity(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_issue(client, project_a, str(user_a.id), title="A", severity="LOW")
        critical_id = _create_issue(
            client, project_a, str(user_a.id), title="B", severity="CRITICAL"
        ).data["id"]

        response = client.get(f"/api/projects/{project_a.id}/issues/?severity=CRITICAL")

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == critical_id

    def test_filter_by_status(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_issue(client, project_a, str(user_a.id), title="A")
        resolved_id = _create_issue(client, project_a, str(user_a.id), title="B").data[
            "id"
        ]
        client.patch(
            f"/api/issues/{resolved_id}/",
            {"status": "RESOLVED", "resolution": "done"},
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/issues/?status=RESOLVED")

        assert response.data["count"] == 1


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIssueIsolation:
    def test_cannot_retrieve_foreign_org_issue(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        issue_id = _create_issue(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/issues/{issue_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_update_foreign_org_issue(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        issue_id = _create_issue(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.patch(
            f"/api/issues/{issue_id}/", {"status": "CLOSED"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_issues(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/issues/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
