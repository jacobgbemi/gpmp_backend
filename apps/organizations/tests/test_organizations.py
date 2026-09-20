"""
Tests for organization endpoints and multi-tenant isolation.

Includes explicit IDOR tests per stage-1.md: User A (Org A) must not be
able to retrieve, modify, or enumerate members of Org B — and the API must
return 404 (existence-hidden), never 403 (existence-confirmed).
"""

import pytest
from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.organizations import services
from apps.organizations.models import Organization, OrganizationMembership, Role

# ---------------------------------------------------------------------------
# Organization creation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrganizationCreation:
    def test_create_organization_via_api(self, user_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post("/api/organizations/", {"name": "New Co"}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Co"
        assert response.data["slug"] == "new-co"

    def test_creator_becomes_organization_admin(self, user_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.post("/api/organizations/", {"name": "New Co"}, format="json")

        assert response.data["my_role"] == "ORGANIZATION_ADMIN"
        membership = OrganizationMembership.objects.get(
            user=user_a, organization_id=response.data["id"]
        )
        assert membership.role == Role.ORGANIZATION_ADMIN

    def test_create_organization_requires_authentication(self, api_client):
        response = api_client.post("/api/organizations/", {"name": "New Co"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_organization_generates_unique_slug_on_name_collision(
        self, user_a, user_b, auth_client
    ):
        client_a, _ = auth_client(user_a)
        client_b, _ = auth_client(user_b)

        first = client_a.post("/api/organizations/", {"name": "Acme"}, format="json")
        second = client_b.post("/api/organizations/", {"name": "Acme"}, format="json")

        assert first.data["slug"] == "acme"
        assert second.data["slug"] != "acme"

    def test_mass_assignment_of_slug_and_role_is_ignored(self, user_a, auth_client):
        """slug/my_role/id are read-only — a client cannot set them directly."""
        client, _ = auth_client(user_a)

        response = client.post(
            "/api/organizations/",
            {
                "name": "New Co",
                "slug": "attacker-chosen-slug",
                "my_role": "PLATFORM_ADMIN",
                "id": "11111111-1111-1111-1111-111111111111",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] != "attacker-chosen-slug"
        assert response.data["my_role"] == "ORGANIZATION_ADMIN"
        assert response.data["id"] != "11111111-1111-1111-1111-111111111111"


# ---------------------------------------------------------------------------
# Membership creation / role assignment / duplicate prevention
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMembership:
    def test_add_member_creates_membership_with_role(self, org_a, user_b):
        membership = services.add_member(
            organization=org_a, user=user_b, role=Role.SITE_INSPECTOR
        )

        assert membership.role == Role.SITE_INSPECTOR
        assert OrganizationMembership.objects.filter(
            user=user_b, organization=org_a
        ).exists()

    def test_add_member_rejects_invalid_role(self, org_a, user_b):
        with pytest.raises(ValidationError):
            services.add_member(organization=org_a, user=user_b, role="NOT_A_REAL_ROLE")

    def test_duplicate_membership_is_prevented(self, org_a, user_a):
        """user_a is already an ORGANIZATION_ADMIN member of org_a (fixture)."""
        with pytest.raises(ValidationError):
            services.add_member(organization=org_a, user=user_a, role=Role.VIEWER)

    def test_duplicate_membership_enforced_at_db_level(self, org_a, user_a):
        """The unique constraint holds even bypassing the service layer."""
        from django.db import IntegrityError, transaction

        with pytest.raises(IntegrityError), transaction.atomic():
            OrganizationMembership.objects.create(
                user=user_a, organization=org_a, role=Role.VIEWER
            )

    def test_change_member_role(self, org_a, user_b):
        membership = services.add_member(organization=org_a, user=user_b, role=Role.VIEWER)

        services.change_member_role(membership=membership, role=Role.PROJECT_MANAGER)
        membership.refresh_from_db()

        assert membership.role == Role.PROJECT_MANAGER

    def test_change_member_role_rejects_invalid_role(self, org_a, user_b):
        membership = services.add_member(organization=org_a, user=user_b, role=Role.VIEWER)

        with pytest.raises(ValidationError):
            services.change_member_role(membership=membership, role="NOT_A_REAL_ROLE")

    @pytest.mark.parametrize("role", [r.value for r in Role])
    def test_every_defined_role_is_assignable(self, org_a, make_user, role):
        member = make_user(email=f"{role.lower()}@example.com")

        membership = services.add_member(organization=org_a, user=member, role=role)

        assert membership.role == role


# ---------------------------------------------------------------------------
# Organization access (own orgs only) / unauthorized access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOrganizationAccess:
    def test_list_only_returns_own_organizations(self, user_a, org_a, org_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get("/api/organizations/")

        ids = {org["id"] for org in response.data["results"]}
        assert ids == {str(org_a.id)}
        assert str(org_b.id) not in ids

    def test_retrieve_own_organization_succeeds(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/organizations/{org_a.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(org_a.id)

    def test_list_requires_authentication(self, api_client):
        response = api_client.get("/api/organizations/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_requires_authentication(self, api_client, org_a):
        response = api_client.get(f"/api/organizations/{org_a.id}/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_organization_returns_404(self, user_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(
            "/api/organizations/00000000-0000-0000-0000-000000000000/"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_non_admin_member_cannot_update_organization(self, org_a, make_user, auth_client):
        member = make_user(email="member@example.com")
        services.add_member(organization=org_a, user=member, role=Role.VIEWER)
        client, _ = auth_client(member)

        response = client.patch(
            f"/api/organizations/{org_a.id}/", {"name": "Renamed"}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_member_can_update_organization(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.patch(
            f"/api/organizations/{org_a.id}/", {"name": "Renamed"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Renamed"

    def test_put_is_not_allowed(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.put(
            f"/api/organizations/{org_a.id}/", {"name": "Renamed"}, format="json"
        )

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_is_not_allowed(self, user_a, org_a, auth_client):
        client, _ = auth_client(user_a)

        response = client.delete(f"/api/organizations/{org_a.id}/")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# Explicit IDOR / cross-organization access tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCrossOrganizationIDOR:
    """
    User A belongs to Org A. User B belongs to Org B.

    User A must not be able to retrieve, modify, or access membership data
    for Org B, and the response must not leak whether Org B exists.
    """

    def test_user_a_cannot_retrieve_org_b(self, user_a, org_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/organizations/{org_b.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_a_cannot_patch_org_b(self, user_a, org_b, auth_client):
        client, _ = auth_client(user_a)
        original_name = org_b.name

        response = client.patch(
            f"/api/organizations/{org_b.id}/", {"name": "Hacked"}, format="json"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        org_b.refresh_from_db()
        assert org_b.name == original_name

    def test_user_a_cannot_list_org_b_members(self, user_a, org_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get(f"/api/organizations/{org_b.id}/members/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_org_b_does_not_appear_in_user_a_list(self, user_a, org_a, org_b, auth_client):
        client, _ = auth_client(user_a)

        response = client.get("/api/organizations/")

        names = {org["name"] for org in response.data["results"]}
        assert org_b.name not in names

    def test_404_response_does_not_leak_org_b_existence(self, user_a, org_b, auth_client):
        """
        A 404 for a real-but-foreign org ID and a 404 for a random UUID must
        be indistinguishable, so an attacker can't use response differences
        to enumerate which organization IDs are real.
        """
        client, _ = auth_client(user_a)

        real_foreign_org = client.get(f"/api/organizations/{org_b.id}/")
        random_uuid = client.get(
            "/api/organizations/00000000-0000-0000-0000-000000000000/"
        )

        assert real_foreign_org.status_code == random_uuid.status_code == 404
        assert real_foreign_org.data == random_uuid.data

    def test_removed_member_immediately_loses_access(self, org_a, make_user, auth_client):
        member = make_user(email="temp@example.com")
        membership = services.add_member(organization=org_a, user=member, role=Role.VIEWER)
        client, _ = auth_client(member)

        # Confirm access while still a member.
        assert client.get(f"/api/organizations/{org_a.id}/").status_code == 200

        membership.delete()

        assert client.get(f"/api/organizations/{org_a.id}/").status_code == 404

    def test_member_of_org_a_cannot_see_org_b_in_their_own_me_response(
        self, user_a, org_a, org_b, auth_client
    ):
        client, _ = auth_client(user_a)

        response = client.get("/api/auth/me/")

        org_ids = {m["organization_id"] for m in response.data["memberships"]}
        assert str(org_b.id) not in org_ids


# ---------------------------------------------------------------------------
# Database integrity
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatabaseIntegrity:
    def test_organization_membership_cascades_on_user_delete(self, org_a, user_a):
        membership_id = OrganizationMembership.objects.get(
            user=user_a, organization=org_a
        ).id

        user_a.delete()

        assert not OrganizationMembership.objects.filter(id=membership_id).exists()

    def test_organization_membership_cascades_on_organization_delete(self, org_a, user_a):
        membership_id = OrganizationMembership.objects.get(
            user=user_a, organization=org_a
        ).id

        org_a.delete()

        assert not OrganizationMembership.objects.filter(id=membership_id).exists()

    def test_organization_slug_is_unique(self):
        Organization.objects.create(name="Foo", slug="foo")

        with pytest.raises(IntegrityError):
            Organization.objects.create(name="Foo Two", slug="foo")

    def test_ids_are_uuids_not_sequential_integers(self, org_a, user_a):
        import uuid

        assert isinstance(org_a.id, uuid.UUID)
        assert isinstance(user_a.id, uuid.UUID)