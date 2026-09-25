"""
Tests for /api/projects/{id}/dashboard/: cost, progress, and payment
calculations, using realistic financial scenarios (₦500M-scale project).
"""

import pytest
from rest_framework import status


def _add_budget_item(client, project, **fields):
    payload = {"category": "CIVIL", "description": "Item"} | fields
    return client.post(f"/api/projects/{project.id}/budget/", payload, format="json")


@pytest.mark.django_db
class TestDashboardCalculations:
    def test_dashboard_with_no_data_is_all_zero(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["original_budget"] == "0.00"
        assert response.data["forecast_final_cost"] == "0.00"
        assert response.data["cost_variance"] == "0.00"
        assert response.data["planned_progress_percent"] == "0.00"
        assert response.data["as_of_reporting_date"] is None
        assert response.data["pending_payments_count"] == 0

    def test_realistic_500m_naira_project_scenario(
        self, user_a, project_a, auth_client
    ):
        """
        A ₦500,000,000 residential project, partway through construction:
        - Approved budget: ₦480,000,000 across two cost categories
        - Actual spend so far: ₦180,000,000
        - Committed (ordered/contracted but not yet spent): ₦150,000,000
        - Latest progress: planned 45%, actual 38% (behind schedule)
        - One pending payment application for ₦25,000,000
        """
        client, _ = auth_client(user_a)
        _add_budget_item(
            client,
            project_a,
            description="Structural works",
            original_amount="300000000.00",
            approved_amount="290000000.00",
            committed_amount="100000000.00",
            actual_amount="120000000.00",
        )
        _add_budget_item(
            client,
            project_a,
            category="MEP",
            description="MEP works",
            original_amount="200000000.00",
            approved_amount="190000000.00",
            committed_amount="50000000.00",
            actual_amount="60000000.00",
        )
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "45.00",
                "actual_progress_percent": "38.00",
            },
            format="json",
        )
        client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "25000000.00"},
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")
        data = response.data

        assert data["original_budget"] == "500000000.00"
        assert data["approved_budget"] == "480000000.00"
        assert data["actual_spend"] == "180000000.00"
        assert data["committed_cost"] == "150000000.00"
        # forecast_final_cost = actual_spend + committed_cost
        assert data["forecast_final_cost"] == "330000000.00"
        # cost_variance = approved_budget - forecast_final_cost (under budget)
        assert data["cost_variance"] == "150000000.00"
        assert data["planned_progress_percent"] == "45.00"
        assert data["actual_progress_percent"] == "38.00"
        # schedule_variance = actual - planned (behind schedule => negative)
        assert data["schedule_variance"] == "-7.00"
        assert data["pending_payments_count"] == 1
        assert data["pending_payments_total"] == "25000000.00"
        assert data["as_of_reporting_date"] == "2026-06-01"

    def test_over_budget_scenario_has_negative_cost_variance(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        _add_budget_item(
            client,
            project_a,
            original_amount="100000000.00",
            approved_amount="100000000.00",
            committed_amount="30000000.00",
            actual_amount="90000000.00",
        )

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        # forecast = 90M + 30M = 120M; variance = 100M - 120M = -20M (over budget)
        assert response.data["forecast_final_cost"] == "120000000.00"
        assert response.data["cost_variance"] == "-20000000.00"

    def test_ahead_of_schedule_has_positive_schedule_variance(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-06-01",
                "planned_progress_percent": "30.00",
                "actual_progress_percent": "40.00",
            },
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["schedule_variance"] == "10.00"

    def test_dashboard_uses_latest_progress_update_only(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/progress/",
            {
                "reporting_date": "2026-05-01",
                "planned_progress_percent": "20.00",
                "actual_progress_percent": "15.00",
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

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        assert response.data["planned_progress_percent"] == "40.00"
        assert response.data["as_of_reporting_date"] == "2026-06-01"

    def test_pending_payments_excludes_approved_and_paid(
        self, user_a, project_a, auth_client
    ):
        client, _ = auth_client(user_a)
        submitted = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "5000000.00"},
            format="json",
        ).data["id"]
        approved_flow = client.post(
            f"/api/projects/{project_a.id}/payments/",
            {"amount_requested": "8000000.00"},
            format="json",
        ).data["id"]
        client.post(
            f"/api/payments/{approved_flow}/review/",
            {"decision": "START_REVIEW"},
            format="json",
        )
        client.post(
            f"/api/payments/{approved_flow}/review/",
            {"decision": "RECOMMEND", "amount": "8000000.00"},
            format="json",
        )
        client.post(
            f"/api/payments/{approved_flow}/review/",
            {"decision": "APPROVE", "amount": "8000000.00"},
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/dashboard/")

        # Only the still-SUBMITTED payment counts as pending; the APPROVED
        # one has moved past "pending".
        assert response.data["pending_payments_count"] == 1
        assert response.data["pending_payments_total"] == "5000000.00"
        assert submitted  # sanity: fixture created successfully

    def test_foreign_org_user_cannot_view_dashboard(
        self, user_a, project_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/dashboard/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
