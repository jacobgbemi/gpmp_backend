"""
Tests for /api/projects/{id}/variations/ and /api/variations/{id}/:
creation, generic status transitions, the dedicated approve action, the
proposed-vs-approved financial distinction on the dashboard, permissions,
and organization isolation.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.variations.models import Variation, VariationStatus


def _create_variation(client, project, **overrides):
    payload = {
        "variation_number": "VO-001",
        "title": "Extra foundation piling",
        "category": "SITE_CONDITION",
        "requested_amount": "15000000.00",
        "estimated_amount": "12000000.00",
    } | overrides
    return client.post(f"/api/projects/{project.id}/variations/", payload, format="json")


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationCreation:
    def test_create_variation(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_variation(client, project_a)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == VariationStatus.PROPOSED
        assert response.data["approved_amount"] is None
        assert response.data["created_by_email"] == user_a.email

    def test_duplicate_variation_number_within_project_rejected(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        _create_variation(client, project_a, variation_number="VO-001")

        response = _create_variation(client, project_a, variation_number="VO-001")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_variation_number_allowed_across_different_projects(
        self, user_a, project_a, make_project, org_a, auth_client
    ):
        other_project = make_project(org_a, project_code="OTHER-PRJ")
        client, _ = auth_client(user_a)

        first = _create_variation(client, project_a, variation_number="VO-001")
        second = _create_variation(client, other_project, variation_number="VO-001")

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED

    def test_negative_requested_amount_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_variation(client, project_a, requested_amount="-100.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_viewer_cannot_create_variation(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = _create_variation(client, project_a)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_create_variation(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = _create_variation(client, project_b)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_status_cannot_be_set_directly_on_create(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_variation(client, project_a, status="APPROVED")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == VariationStatus.PROPOSED


# ---------------------------------------------------------------------------
# Generic status transitions (not approval)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationStatusTransitions:
    def test_proposed_to_under_review_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "UNDER_REVIEW"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "UNDER_REVIEW"

    def test_proposed_to_rejected_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "REJECTED"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_proposed_to_implemented_is_invalid(self, user_a, project_a, auth_client):
        """Cannot skip straight to IMPLEMENTED without going through APPROVED."""
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "IMPLEMENTED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_status_cannot_be_set_to_approved_via_patch(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "APPROVED"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        variation = Variation.objects.get(id=variation_id)
        assert variation.status == VariationStatus.PROPOSED
        assert variation.approved_amount is None

    def test_rejected_is_not_immediately_terminal_can_close(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.patch(f"/api/variations/{variation_id}/", {"status": "REJECTED"}, format="json")

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "CLOSED"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

    def test_closed_is_terminal(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.patch(f"/api/variations/{variation_id}/", {"status": "REJECTED"}, format="json")
        client.patch(f"/api/variations/{variation_id}/", {"status": "CLOSED"}, format="json")

        response = client.patch(
            f"/api/variations/{variation_id}/", {"status": "UNDER_REVIEW"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Approval action
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationApproval:
    def test_approve_from_proposed(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "13000000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == VariationStatus.APPROVED
        assert response.data["approved_amount"] == "13000000.00"
        assert response.data["approved_by_email"] == user_a.email
        assert response.data["approved_date"] is not None

    def test_approve_from_under_review(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.patch(f"/api/variations/{variation_id}/", {"status": "UNDER_REVIEW"}, format="json")

        response = client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "13000000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_cannot_approve_a_rejected_variation(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.patch(f"/api/variations/{variation_id}/", {"status": "REJECTED"}, format="json")

        response = client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "1.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_approve_an_already_approved_variation(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "13000000.00"},
            format="json",
        )

        response = client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "14000000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_approve_without_amount_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]

        response = client.post(
            f"/api/variations/{variation_id}/approve/", {}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_project_manager_cannot_approve_variation(
        self, user_a, org_a, project_a, make_user, auth_client
    ):
        """Separation of duties, mirroring payment review."""
        pm = make_user(email="pm2@example.com")
        org_services.add_member(organization=org_a, user=pm, role=Role.PROJECT_MANAGER)
        admin_client, _ = auth_client(user_a)
        variation_id = _create_variation(admin_client, project_a).data["id"]

        pm_client, _ = auth_client(pm)
        response = pm_client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "1.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_project_controls_can_approve_variation(
        self, user_a, org_a, project_a, make_user, auth_client
    ):
        controls = make_user(email="controls@example.com")
        org_services.add_member(organization=org_a, user=controls, role=Role.PROJECT_CONTROLS)
        admin_client, _ = auth_client(user_a)
        variation_id = _create_variation(admin_client, project_a).data["id"]

        controls_client, _ = auth_client(controls)
        response = controls_client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "1.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Proposed exposure vs approved financial impact (dashboard)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationFinancialImpact:
    def test_proposed_variation_does_not_affect_approved_budget(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        _create_variation(client, project_a, estimated_amount="12000000.00")

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["approved_variations_total"] == "0.00"
        assert response.data["pending_variations_exposure"] == "12000000.00"
        assert response.data["revised_approved_budget"] == "0.00"

    def test_approved_variation_increases_revised_approved_budget(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(client, project_a).data["id"]
        client.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "13000000.00"},
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["approved_variations_total"] == "13000000.00"
        assert response.data["pending_variations_exposure"] == "0.00"
        assert response.data["revised_approved_budget"] == "13000000.00"

    def test_rejected_variation_never_counted_as_approved_or_pending(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        variation_id = _create_variation(
            client, project_a, estimated_amount="12000000.00"
        ).data["id"]

        client.patch(f"/api/variations/{variation_id}/", {"status": "REJECTED"}, format="json")

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["approved_variations_total"] == "0.00"
        assert response.data["pending_variations_exposure"] == "0.00"

    def test_multiple_variations_in_different_states_aggregate_correctly(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        approved_id = _create_variation(
            client, project_a, variation_number="VO-A"
        ).data["id"]
        client.post(
            f"/api/variations/{approved_id}/approve/",
            {"approved_amount": "10000000.00"},
            format="json",
        )
        _create_variation(
            client, project_a, variation_number="VO-B", estimated_amount="5000000.00"
        )
        rejected_id = _create_variation(
            client, project_a, variation_number="VO-C", estimated_amount="9999999.00"
        ).data["id"]
        client.patch(f"/api/variations/{rejected_id}/", {"status": "REJECTED"}, format="json")

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["approved_variations_total"] == "10000000.00"
        assert response.data["pending_variations_exposure"] == "5000000.00"
        assert response.data["revised_approved_budget"] == "10000000.00"


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationIsolation:
    def test_cannot_retrieve_foreign_org_variation(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        variation_id = _create_variation(client_b, project_b).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/variations/{variation_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_approve_foreign_org_variation(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        variation_id = _create_variation(client_b, project_b).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.post(
            f"/api/variations/{variation_id}/approve/",
            {"approved_amount": "1.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_variations(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/variations/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationFiltering:
    def test_filter_by_status(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_variation(client, project_a, variation_number="VO-A")
        rejected_id = _create_variation(client, project_a, variation_number="VO-B").data["id"]
        client.patch(f"/api/variations/{rejected_id}/", {"status": "REJECTED"}, format="json")

        response = client.get(f"/api/projects/{project_a.id}/variations/?status=REJECTED")

        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == rejected_id

    def test_filter_by_category(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        _create_variation(client, project_a, variation_number="VO-A", category="DESIGN_CHANGE")
        _create_variation(client, project_a, variation_number="VO-B", category="SITE_CONDITION")

        response = client.get(
            f"/api/projects/{project_a.id}/variations/?category=DESIGN_CHANGE"
        )

        assert response.data["count"] == 1
        assert response.data["results"][0]["category"] == "DESIGN_CHANGE"


# ---------------------------------------------------------------------------
# Money precision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVariationMoneyPrecision:
    def test_amounts_preserve_two_decimal_places(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = _create_variation(client, project_a, requested_amount="12345678.99")

        variation = Variation.objects.get(id=response.data["id"])
        assert variation.requested_amount == Decimal("12345678.99")
