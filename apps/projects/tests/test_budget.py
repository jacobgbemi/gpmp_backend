"""
Tests for /api/projects/{id}/budget/: item creation, computed totals,
money precision, permissions, and organization isolation.
"""

from decimal import Decimal

import pytest
from rest_framework import status

from apps.organizations import services as org_services
from apps.organizations.models import Role
from apps.projects.models import BudgetItem


@pytest.mark.django_db
class TestBudgetItemCreation:
    def test_add_budget_item(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/budget/",
            {
                "category": "CIVIL",
                "description": "Foundation works",
                "original_amount": "100000000.00",
                "approved_amount": "100000000.00",
                "committed_amount": "60000000.00",
                "actual_amount": "40000000.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["category"] == "CIVIL"
        assert BudgetItem.objects.filter(description="Foundation works").exists()

    def test_budget_item_defaults_to_zero_amounts(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/budget/",
            {"category": "MEP", "description": "MEP allowance"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["original_amount"] == "0.00"

    def test_negative_amount_rejected(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_a.id}/budget/",
            {
                "category": "CIVIL",
                "description": "Bad item",
                "original_amount": "-500.00",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_viewer_cannot_add_budget_item(self, org_a, project_a, make_user, auth_client):
        viewer = make_user(email="viewer@example.com")
        org_services.add_member(organization=org_a, user=viewer, role=Role.VIEWER)
        client, _ = auth_client(viewer)

        response = client.post(
            f"/api/projects/{project_a.id}/budget/",
            {"category": "CIVIL", "description": "X", "original_amount": "100.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_foreign_org_user_cannot_add_budget_item(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.post(
            f"/api/projects/{project_b.id}/budget/",
            {"category": "CIVIL", "description": "X", "original_amount": "100.00"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestBudgetTotals:
    def test_totals_sum_across_multiple_items(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/budget/",
            {
                "category": "CIVIL",
                "description": "Item 1",
                "original_amount": "100000000.00",
                "approved_amount": "100000000.00",
                "committed_amount": "60000000.00",
                "actual_amount": "40000000.00",
            },
            format="json",
        )
        client.post(
            f"/api/projects/{project_a.id}/budget/",
            {
                "category": "MEP",
                "description": "Item 2",
                "original_amount": "50000000.00",
                "approved_amount": "45000000.00",
                "committed_amount": "20000000.00",
                "actual_amount": "10000000.00",
            },
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/budget/")

        assert response.data["original_total"] == "150000000.00"
        assert response.data["approved_total"] == "145000000.00"
        assert response.data["committed_total"] == "80000000.00"
        assert response.data["actual_total"] == "50000000.00"
        assert len(response.data["items"]) == 2

    def test_totals_are_zero_with_no_items(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_a.id}/budget/")

        assert response.data["original_total"] == "0.00"
        assert response.data["items"] == []

    def test_budget_totals_precise_to_the_cent(self, user_a, project_a, auth_client):
        client, _ = auth_client(user_a)
        client.post(
            f"/api/projects/{project_a.id}/budget/",
            {"category": "CIVIL", "description": "A", "original_amount": "0.10"},
            format="json",
        )
        client.post(
            f"/api/projects/{project_a.id}/budget/",
            {"category": "CIVIL", "description": "B", "original_amount": "0.20"},
            format="json",
        )

        response = client.get(f"/api/projects/{project_a.id}/budget/")

        # Decimal arithmetic: 0.10 + 0.20 must be exactly 0.30, never the
        # 0.30000000000000004 float artifact.
        assert response.data["original_total"] == "0.30"
        assert Decimal(response.data["original_total"]) == Decimal("0.30")

    def test_foreign_org_user_cannot_view_budget(self, user_a, project_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/projects/{project_b.id}/budget/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
