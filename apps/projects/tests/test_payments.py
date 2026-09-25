"""
Tests for payment applications: creation, the review state machine
(PaymentService.review), the requested/recommended/approved/paid
distinction, review-role restrictions, and organization isolation.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.projects.models import PaymentApplication, PaymentStatus


def _review(client, payment_id, decision, amount=None, notes=None):
    payload = {"decision": decision}
    if amount is not None:
        payload["amount"] = amount
    if notes is not None:
        payload["notes"] = notes
    return client.post(f"/api/payments/{payment_id}/review/", payload, format="json")


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentCreation:
    def test_create_payment(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == PaymentStatus.SUBMITTED
        assert response.data["application_number"] == "PA-0001"
        assert response.data["amount_recommended"] is None
        assert response.data["amount_approved"] is None
        assert response.data["amount_paid"] == "0.00"

    def test_application_numbers_increment_per_project(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)

        first = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        )
        second = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "2000.00"},
            format="json",
        )

        assert first.data["application_number"] == "PA-0001"
        assert second.data["application_number"] == "PA-0002"

    def test_negative_amount_requested_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "-500.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_viewer_cannot_create_payment(
        self, org_a, project_a, make_user, auth_client
    ):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_create_payment(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_b.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_no_payment_can_exist_without_a_project(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        )

        payment = PaymentApplication.objects.get(project=project_a)
        assert payment.project_id == project_a.id
        assert PaymentApplication._meta.get_field("project").null is False


# ---------------------------------------------------------------------------
# Requested / recommended / approved / paid distinction
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAmountDistinction:
    def test_all_four_amounts_are_independent_fields(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]

        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="18000000.00")
        _review(client, payment_id, "APPROVE", amount="17000000.00")
        response = _review(client, payment_id, "RECORD_PAYMENT", amount="10000000.00")

        # Four genuinely different numbers, none of them collapsed together.
        assert response.data["amount_requested"] == "20000000.00"
        assert response.data["amount_recommended"] == "18000000.00"
        assert response.data["amount_approved"] == "17000000.00"
        assert response.data["amount_paid"] == "10000000.00"

    def test_recommended_can_be_less_than_requested(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]
        _review(client, payment_id, "START_REVIEW")

        response = _review(client, payment_id, "RECOMMEND", amount="15000000.00")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["amount_recommended"] == "15000000.00"

    def test_recommended_cannot_exceed_requested(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]
        _review(client, payment_id, "START_REVIEW")

        response = _review(client, payment_id, "RECOMMEND", amount="25000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_approved_cannot_exceed_recommended(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]
        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="15000000.00")

        response = _review(client, payment_id, "APPROVE", amount="16000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_total_paid_cannot_exceed_approved(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]
        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="15000000.00")
        _review(client, payment_id, "APPROVE", amount="15000000.00")

        response = _review(client, payment_id, "RECORD_PAYMENT", amount="16000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_partial_payments_accumulate_to_paid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        create = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "20000000.00"},
            format="json",
        )
        payment_id = create.data["id"]
        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="18000000.00")
        _review(client, payment_id, "APPROVE", amount="18000000.00")

        first = _review(client, payment_id, "RECORD_PAYMENT", amount="10000000.00")
        second = _review(client, payment_id, "RECORD_PAYMENT", amount="8000000.00")

        assert first.data["status"] == PaymentStatus.PARTIALLY_PAID
        assert first.data["amount_paid"] == "10000000.00"
        assert second.data["status"] == PaymentStatus.PAID
        assert second.data["amount_paid"] == "18000000.00"


# ---------------------------------------------------------------------------
# Valid / invalid transitions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentReviewTransitions:
    def _create(self, client, project):
        return client.post(
            f"/api/projects/{project.id}/payments/",
            {"amount_requested": "10000000.00"},
            format="json",
        ).data["id"]

    def test_full_happy_path(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)

        assert _review(client, payment_id, "START_REVIEW").status_code == 200
        assert (
            _review(client, payment_id, "RECOMMEND", amount="9000000.00").status_code
            == 200
        )
        assert (
            _review(client, payment_id, "APPROVE", amount="9000000.00").status_code
            == 200
        )
        response = _review(client, payment_id, "RECORD_PAYMENT", amount="9000000.00")
        assert response.status_code == 200
        assert response.data["status"] == PaymentStatus.PAID

    def test_cannot_approve_before_recommend(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)
        _review(client, payment_id, "START_REVIEW")

        response = _review(client, payment_id, "APPROVE", amount="9000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_recommend_before_start_review(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)

        response = _review(client, payment_id, "RECOMMEND", amount="9000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_record_payment_before_approve(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)
        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="9000000.00")

        response = _review(client, payment_id, "RECORD_PAYMENT", amount="9000000.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_a_paid_payment(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)
        _review(client, payment_id, "START_REVIEW")
        _review(client, payment_id, "RECOMMEND", amount="9000000.00")
        _review(client, payment_id, "APPROVE", amount="9000000.00")
        _review(client, payment_id, "RECORD_PAYMENT", amount="9000000.00")

        response = _review(client, payment_id, "RECORD_PAYMENT", amount="1.00")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_a_rejected_payment(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)
        _review(client, payment_id, "START_REVIEW")

        _review(client, payment_id, "REJECT", notes="Missing documentation")
        response = _review(client, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_requires_notes(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)

        response = _review(client, payment_id, "REJECT", notes="")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reject_from_submitted_is_valid(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)

        response = _review(client, payment_id, "REJECT", notes="Duplicate application")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == PaymentStatus.REJECTED

    def test_unknown_decision_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)

        response = _review(client, payment_id, "TELEPORT")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_recommend_without_amount_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        payment_id = self._create(client, project_a)
        _review(client, payment_id, "START_REVIEW")

        response = _review(client, payment_id, "RECOMMEND")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Review-role restriction (separation of duties)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentReviewPermissions:
    def test_project_manager_cannot_review_payments(
        self, org_a, project_a, make_user, auth_client
    ):
        """
        Separation of duties: PROJECT_MANAGER can create/manage a project
        but must not also review its payments.
        """
        pm = make_user(email="pm@example.com")
        org_services.add_member(organization=org_a, user=pm, role=Role.PROJECT_MANAGER)
        client, _ = auth_client(pm)
        payment_id = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        response = _review(client, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_project_controls_can_review_payments(
        self, org_a, project_a, make_user, auth_client
    ):
        controls = make_user(email="controls@example.com")
        org_services.add_member(
            organization=org_a, user=controls, role=Role.PROJECT_CONTROLS
        )
        client, _ = auth_client(controls)
        payment_id = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        response = _review(client, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_200_OK

    def test_organization_admin_can_review_payments(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(
            user_a
        )  # org_a fixture makes user_a an ORGANIZATION_ADMIN
        payment_id = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        response = _review(client, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_200_OK

    def test_viewer_cannot_review_payments(
        self, user_a, org_a, project_a, make_user, auth_client
    ):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        admin_client, _ = auth_client(user_a)
        payment_id = admin_client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        viewer_client, _ = auth_client(viewer)
        response = _review(viewer_client, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# Organization isolation / IDOR
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentIsolation:
    def test_cannot_retrieve_foreign_org_payment(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        payment_id = client_b.post(
            f"/api/projects/{project_b.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        client_a, _ = auth_client(user_a)
        response = client_a.get(f"/api/payments/{payment_id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_review_foreign_org_payment(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        payment_id = client_b.post(
            f"/api/projects/{project_b.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        client_a, _ = auth_client(user_a)
        response = _review(client_a, payment_id, "START_REVIEW")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_foreign_org_project_payments(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/payments/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_payment_amount_unaffected_by_failed_foreign_review_attempt(
        self, user_a, project_b, user_b, auth_client
    ):
        client_b, _ = auth_client(user_b)
        payment_id = client_b.post(
            f"/api/projects/{project_b.id}/payments/",
            {"amount_requested": "1000.00"},
            format="json",
        ).data["id"]

        client_a, _ = auth_client(user_a)
        _review(client_a, payment_id, "REJECT", notes="hostile takeover")

        payment = PaymentApplication.objects.get(id=payment_id)
        assert payment.status == PaymentStatus.SUBMITTED


# ---------------------------------------------------------------------------
# Money precision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentMoneyPrecision:
    def test_amounts_preserve_two_decimal_places(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "12345678.99"},
            format="json",
        )

        payment = PaymentApplication.objects.get(id=response.data["id"])
        assert payment.amount_requested == Decimal("12345678.99")
        assert response.data["amount_requested"] == "12345678.99"
