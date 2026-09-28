import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.projects.models import Project

LIST_URL = "/api/projects/"


def _project(org, name, code, status="ACTIVE", **extra):
    return Project.objects.create(
        organization=org,
        name=name,
        project_code=code,
        contract_value="1000000.00",
        status=status,
        **extra,
    )


@pytest.fixture
def client_and_org(db):
    user = User.objects.create_user(email="owner@example.com", password="x")
    org = Organization.objects.create(name="Org", slug="org")
    OrganizationMembership.objects.create(
        user=user, organization=org, role=Role.ORGANIZATION_ADMIN
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client, org


@pytest.fixture
def seeded(client_and_org):
    client, org = client_and_org
    _project(org, "Luxury Residence", "LRL-001", "ACTIVE", location="Lekki, Lagos")
    _project(org, "Escravos Pipeline", "EPU-002", "PLANNING", client_name="Chevron")
    _project(org, "Harbour Terminal", "HBT-003", "COMPLETED")
    return client, org


def _names(response):
    return sorted(p["name"] for p in response.data["results"])


@pytest.mark.django_db
class TestProjectListFilters:
    def test_no_params_returns_everything(self, seeded):
        client, _ = seeded
        assert len(client.get(LIST_URL).data["results"]) == 3

    def test_filter_by_status(self, seeded):
        client, _ = seeded
        response = client.get(LIST_URL, {"status": "PLANNING"})
        assert response.status_code == 200
        assert _names(response) == ["Escravos Pipeline"]

    def test_search_by_name_is_case_insensitive(self, seeded):
        client, _ = seeded
        assert _names(client.get(LIST_URL, {"search": "luxury"})) == [
            "Luxury Residence"
        ]

    def test_search_by_project_code(self, seeded):
        client, _ = seeded
        assert _names(client.get(LIST_URL, {"search": "hbt-003"})) == [
            "Harbour Terminal"
        ]

    def test_search_by_location_and_client(self, seeded):
        client, _ = seeded
        assert _names(client.get(LIST_URL, {"search": "lekki"})) == ["Luxury Residence"]
        assert _names(client.get(LIST_URL, {"search": "chevron"})) == [
            "Escravos Pipeline"
        ]

    def test_search_and_status_combine(self, seeded):
        client, _ = seeded
        response = client.get(LIST_URL, {"search": "luxury", "status": "PLANNING"})
        assert response.data["results"] == []
        assert response.data["count"] == 0

    def test_search_with_no_match_returns_empty_page(self, seeded):
        client, _ = seeded
        response = client.get(LIST_URL, {"search": "zzz-nothing"})
        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_filtering_never_leaks_other_organizations(self, seeded):
        client, _ = seeded
        other = Organization.objects.create(name="Other", slug="other")
        _project(other, "Luxury Secret", "SEC-999", "ACTIVE")
        response = client.get(LIST_URL, {"search": "luxury"})
        assert _names(response) == ["Luxury Residence"]

    def test_default_ordering_is_newest_first(self, seeded):
        client, _ = seeded
        codes = [p["project_code"] for p in client.get(LIST_URL).data["results"]]
        assert codes == ["HBT-003", "EPU-002", "LRL-001"]

    def test_status_param_does_not_break_nested_endpoints(self, seeded):
        """?status= on a detail/nested URL must not filter the project itself."""
        client, _ = seeded
        project = Project.objects.get(project_code="LRL-001")
        for suffix in ("", "payments/", "progress/", "dashboard/"):
            url = f"{LIST_URL}{project.id}/{suffix}"
            assert client.get(url, {"status": "PAID"}).status_code == 200, suffix