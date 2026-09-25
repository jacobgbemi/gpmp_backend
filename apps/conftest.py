"""
Shared pytest fixtures for tests under apps/.

Lives here (rather than under a single app's tests/) so both
apps/accounts/tests/ and apps/organizations/tests/ can use the same
fixtures — pytest resolves conftest.py by walking up from the test file to
the rootdir.
"""

import itertools
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects.models import Project, ProjectBudget, ProjectType

DEFAULT_PASSWORD = "StrongPass123!"
_project_code_counter = itertools.count(1)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    def _make_user(email="user@example.com", password=DEFAULT_PASSWORD, **kwargs):
        return User.objects.create_user(email=email, password=password, **kwargs)

    return _make_user


@pytest.fixture
def user_a(make_user):
    return make_user(email="a@example.com", first_name="Alice", last_name="A")


@pytest.fixture
def user_b(make_user):
    return make_user(email="b@example.com", first_name="Bob", last_name="B")


@pytest.fixture
def org_a(db, user_a):
    organization = Organization.objects.create(name="Org A", slug="org-a")
    OrganizationMembership.objects.create(
        user=user_a, organization=organization, role=Role.ORGANIZATION_ADMIN
    )
    return organization


@pytest.fixture
def org_b(db, user_b):
    organization = Organization.objects.create(name="Org B", slug="org-b")
    OrganizationMembership.objects.create(
        user=user_b, organization=organization, role=Role.ORGANIZATION_ADMIN
    )
    return organization


@pytest.fixture
def auth_client():
    """
    Factory fixture: auth_client(user) -> (APIClient, token_pair_dict)

    The client carries a valid Bearer access token obtained through the
    real /api/auth/token/ endpoint (not a shortcut), so tests exercise the
    actual login path.
    """

    def _auth_client(user, password=DEFAULT_PASSWORD):
        client = APIClient()
        response = client.post(
            "/api/auth/token/",
            {"email": user.email, "password": password},
            format="json",
        )
        assert response.status_code == 200, response.data
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client, response.data

    return _auth_client


@pytest.fixture
def make_project(db):
    def _make_project(organization, **kwargs):
        kwargs.setdefault("name", "Lekki Residence")
        kwargs.setdefault("project_code", f"PRJ-{next(_project_code_counter):04d}")
        kwargs.setdefault("project_type", ProjectType.RESIDENTIAL)
        kwargs.setdefault("contract_value", Decimal("500000000.00"))
        project = Project.objects.create(organization=organization, **kwargs)
        ProjectBudget.objects.get_or_create(project=project)
        return project

    return _make_project


@pytest.fixture
def project_a(make_project, org_a):
    return make_project(org_a)


@pytest.fixture
def project_b(make_project, org_b):
    return make_project(org_b)
