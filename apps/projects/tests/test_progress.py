"""
Tests for /api/projects/{id}/progress/: creation, immutable history,
percentage validation, duplicate reporting-date prevention, and isolation.
"""

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.projects.models import ProgressUpdate


@pytest.mark.django_db
class TestProgressCreation:
    def test_add_progress_update(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "40.00",
                "actual_progress_percent": "35.00",
                "notes": "Behind due to rain",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["progress_variance_percent"] == -5.0
        assert response.data["submitted_by_email"] == user_a.email

    def test_progress_update_records_submitter(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "40.00",
                "actual_progress_percent": "35.00",
            },
            format="json",
        )

        update = ProgressUpdate.objects.get(project=project_a)
        assert update.submitted_by == user_a

    def test_viewer_cannot_submit_progress(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "40.00",
                "actual_progress_percent": "35.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProgressValidation:
    @pytest.mark.parametrize("field", ["planned_progress_percent", "actual_progress_percent"])
    def test_percent_over_100_rejected(self, user_a, project_a, auth_client, field):
        client, _ = auth_client(user_a)
        payload = {
            "reporting_date": "2026-06-01",
            "planned_progress_percent": "40.00",
            "actual_progress_percent": "35.00",
        }
        payload[field] = "150.00"

        response = client.post(
            f"/api/projects/{project_a.id}/progress/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("field", ["planned_progress_percent", "actual_progress_percent"])
    def test_negative_percent_rejected(self, user_a, project_a, auth_client, field):
        client, _ = auth_client(user_a)
        payload = {
            "reporting_date": "2026-06-01",
            "planned_progress_percent": "40.00",
            "actual_progress_percent": "35.00",
        }
        payload[field] = "-10.00"

        response = client.post(
            f"/api/projects/{project_a.id}/progress/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_zero_and_hundred_percent_are_valid_boundaries(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "0.00",
                "actual_progress_percent": "100.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_duplicate_reporting_date_for_same_project_rejected(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        payload = {
            "reporting_date": "2026-06-01",
            "planned_progress_percent": "40.00",
            "actual_progress_percent": "35.00",
        }
        client.post(f"/api/projects/{project_a.id}/progress/", payload, format="json")

        response = client.post(
            f"/api/projects/{project_a.id}/progress/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_reporting_date_allowed_across_different_projects(
        self, user_a, project_a, make_project, org_a, auth_client
    ):
        other_project = make_project(org_a, project_code="OTHER-001")
        client, _ = auth_client(user_a)
        payload = {
            "reporting_date": "2026-06-01",
            "planned_progress_percent": "40.00",
            "actual_progress_percent": "35.00",
        }

        first = client.post(f"/api/projects/{project_a.id}/progress/", payload, format="json")
        second = client.post(
            f"/api/projects/{other_project.id}/progress/", payload, format="json"
        )

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestProgressHistory:
    def test_history_preserved_across_multiple_updates(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-05-01",
                "planned_progress_percent": "20.00",
                "actual_progress_percent": "18.00",
            },
            format="json",
        )
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "40.00",
                "actual_progress_percent": "35.00",
            },
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/progress/")

        assert response.data["count"] == 2
        # Most recent reporting_date first.
        dates = [row["reporting_date"] for row in response.data["results"]]
        assert dates == ["2026-06-01", "2026-05-01"]

    def test_progress_update_has_no_patch_endpoint(self, user_a, project_a, auth_client):
        """Progress history is immutable — there is no update endpoint."""
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "40.00",
                "actual_progress_percent": "35.00",
            },
            format="json",
        )
        update_id = create.data["id"]

        response = client.patch(
            f"/api/projects/{project_a.id}/progress/{update_id}/",
            {"actual_progress_percent": "99.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_foreign_org_user_cannot_view_progress(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/progress/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
