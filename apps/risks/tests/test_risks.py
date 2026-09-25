"""
Tests for /api/projects/{id}/risks/ and /api/risks/{id}/: creation,
automatic risk scoring, status transitions, owner-must-be-member
validation, permissions, filtering, and organization isolation.
"""

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.risks.models import Risk


def _create_risk(client, project, owner_id, **overrides):
    payload = {
        "title": "Rainy season delay",
        "category": "SCHEDULE",
        "probability": 4,
        "impact": 5,
        "owner": owner_id,
        "response": "MITIGATE",
        "mitigation": "Add weather buffer to schedule",
    } | overrides
    return client.post(f"/api/projects/{project.id}/risks/", payload, format="json")


# ---------------------------------------------------------------------------
# Creation & scoring
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRiskCreationAndScoring:
    def test_create_risk(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_risk(client, project_a, str(user_a.id))

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "OPEN"

    def test_risk_score_is_probability_times_impact(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)

        response = _create_risk(
            client, project_a, str(user_a.id), probability=3, impact=4
        )

        assert response.data["risk_score"] == 12

    @pytest.mark.parametrize(
        ("probability", "impact", "expected_level"),
        [
            (1, 1, "LOW"),
            (2, 2, "MEDIUM"),
            (2, 4, "HIGH"),
            (5, 5, "CRITICAL"),
        ],
    )
    def test_risk_level_banding(
        self, user_a, project_a, auth_client, probability, impact, expected_level
    ):
        client, _ = auth_client(user_a)

        response = _create_risk(
            client, project_a, str(user_a.id), probability=probability, impact=impact
        )

        assert response.data["risk_level"] == expected_level

    def test_risk_score_is_never_client_settable(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_risk(
            client, project_a, str(user_a.id), probability=1, impact=1, risk_score=25
        )

        # Even if the client tries to smuggle risk_score=25 in, the real
        # score (1*1=1) is what gets stored — the field is not writable.
        assert response.data["risk_score"] == 1

    @pytest.mark.parametrize("field", ["probability", "impact"])
    def test_score_input_above_5_rejected(self, user_a, project_a, auth_client, field):
        client, _ = auth_client(user_a)

        response = _create_risk(client, project_a, str(user_a.id), **{field: 6})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize("field", ["probability", "impact"])
    def test_score_input_below_1_rejected(self, user_a, project_a, auth_client, field):
        client, _ = auth_client(user_a)

        response = _create_risk(client, project_a, str(user_a.id), **{field: 0})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_owner_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payload = {
            "title": "X",
            "probability": 2,
            "impact": 2,
        }

        response = client.post(
            f"/api/projects/{project_a.id}/risks/", payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_owner_must_be_organization_member(
        self, user_a, project_a, user_b, auth_client
    ):
        """user_b belongs to a different organization entirely."""
        client, _ = auth_client(user_a)

        response = _create_risk(client, project_a, str(user_b.id))

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_viewer_cannot_create_risk(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _create_risk(client, project_a, str(viewer.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_create_risk(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_risk(client, project_b, str(user_a.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRiskStatusTransitions:
    def test_open_to_mitigating_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/risks/{risk_id}/", {"status": "MITIGATING"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_open_to_closed_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(client, project_a, str(user_a.id)).data["id"]

        response = client.patch(
            f"/api/risks/{risk_id}/", {"status": "CLOSED"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_closed_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(client, project_a, str(user_a.id)).data["id"]
        client.patch(f"/api/risks/{risk_id}/", {"status": "CLOSED"}, format="json")

        response = client.patch(
            f"/api/risks/{risk_id}/", {"status": "OPEN"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mitigating_can_move_to_monitoring_and_back(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(client, project_a, str(user_a.id)).data["id"]
        client.patch(f"/api/risks/{risk_id}/", {"status": "MITIGATING"}, format="json")

        to_monitoring = client.patch(
            f"/api/risks/{risk_id}/", {"status": "MONITORING"}, format="json"
        )
        back_to_mitigating = client.patch(
            f"/api/risks/{risk_id}/", {"status": "MITIGATING"}, format="json"
        )

        assert to_monitoring.status_code == 200
        assert back_to_mitigating.status_code == 200


# ---------------------------------------------------------------------------
# Updating probability/impact recomputes the score
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRiskScoreRecomputation:
    def test_updating_probability_recomputes_score(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(
            client, project_a, str(user_a.id), probability=2, impact=2
        ).data["id"]
        assert Risk.objects.get(id=risk_id).risk_score == 4

        response = client.patch(
            f"/api/risks/{risk_id}/", {"probability": 5}, format="json"
        )

        assert response.data["risk_score"] == 10

    def test_updating_impact_recomputes_score(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        risk_id = _create_risk(
            client, project_a, str(user_a.id), probability=2, impact=2
        ).data["id"]

        response = client.patch(f"/api/risks/{risk_id}/", {"impact": 5}, format="json")

        assert response.data["risk_score"] == 10


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRiskFiltering:
    def test_filter_by_status(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_risk(client, project_a, str(user_a.id), title="A")
        closed_id = _create_risk(client, project_a, str(user_a.id), title="B").data[
            "id"
        ]
        client.patch(f"/api/risks/{closed_id}/", {"status": "CLOSED"}, format="json")

        response = client.get(f"/api/projects/{project_a.id}/risks/?status=CLOSED")

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == closed_id

    def test_filter_by_owner(self, user_a, org_a, project_a, make_user, auth_client):
        other_member = make_user(email="other@example.com")
        org_services.add_member(organization=org_a, user=other_member, role=Role.VIEWER)
        client, _ = auth_client(user_a)
        _create_risk(client, project_a, str(user_a.id), title="Mine")
        theirs_id = _create_risk(
            client, project_a, str(other_member.id), title="Theirs"
        ).data["id"]

        response = client.get(
            f"/api/projects/{project_a.id}/risks/?owner={other_member.id}"
        )

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == theirs_id


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRiskIsolation:
    def test_cannot_retrieve_foreign_org_risk(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        risk_id = _create_risk(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/risks/{risk_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_update_foreign_org_risk(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        risk_id = _create_risk(client_b, project_b, str(user_b.id)).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.patch(
            f"/api/risks/{risk_id}/", {"status": "CLOSED"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_risks(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/risks/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
