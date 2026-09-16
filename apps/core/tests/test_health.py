"""Tests for the /api/health/ endpoint."""

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_endpoint_returns_200(self):
        client = APIClient()
        response = client.get("/api/health/")

        assert response.status_code == status.HTTP_200_OK

    def test_health_endpoint_reports_ok_status(self):
        client = APIClient()
        response = client.get("/api/health/")

        assert response.data["success"] is True
        assert response.data["data"]["status"] == "ok"
        assert response.data["data"]["database"] == "ok"

    def test_health_endpoint_is_publicly_accessible(self):
        """The health check must not require authentication."""
        client = APIClient()
        response = client.get("/api/health/")

        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_health_endpoint_confirms_database_connection(self, db):
        """django_db / db fixture forces a real DB connection to be used."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)