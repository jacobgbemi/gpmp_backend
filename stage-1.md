Build Backend Stage 1 of GlintPM Private.

GlintPM Private is an Owner-Side Project Control & Assurance platform for high-value construction projects.

Follow this workflow strictly:

1. Define business problem
2. Design data model
3. Design API
4. Implement backend
5. Write tests
6. Test API with Postman
7. Build relevant frontend
8. Test failure states
9. Check database integrity
10. Review security/permissions
11. Git commit
12. Document important decisions

Do not implement Projects, Payments, Risks, Variations, Inspections, Documents or Reports yet.

========================================
1. BUSINESS PROBLEM
========================================

GlintPM Private needs secure identity and organization-level access control.

A user may belong to one or more organizations.

Every organization represents a business/client environment.

Users must never access another organization's data.

This stage establishes the multi-tenant security foundation.

========================================
2. DATA MODEL
========================================

Create:

User
Organization
OrganizationMembership

User:

- UUID primary/public ID
- email
- password
- first_name
- last_name
- is_active
- is_staff
- timestamps

Use a custom Django User based on AbstractUser.

Email should be the login identifier.

Organization:

- UUID
- name
- slug/code where appropriate
- timestamps

OrganizationMembership:

- UUID
- user
- organization
- role
- timestamps

Roles:

PLATFORM_ADMIN
ORGANIZATION_ADMIN
PROJECT_MANAGER
PROJECT_CONTROLS
SITE_INSPECTOR
CONSULTANT
CLIENT_OWNER
VIEWER

Add appropriate database constraints.

A user should not have duplicate membership in the same organization.

========================================
3. API DESIGN
========================================

Implement:

POST /api/auth/token/
POST /api/auth/token/refresh/
GET /api/auth/me/

Organization endpoints:

GET /api/organizations/
GET /api/organizations/{id}/
POST /api/organizations/
PATCH /api/organizations/{id}/

Do not expose organizations a user does not belong to.

========================================
4. IMPLEMENTATION
========================================

Implement:

- custom User
- JWT authentication
- organization membership
- role handling
- permissions
- serializers
- views/viewsets
- services where business logic is required
- selectors for queries
- URL routing

Use UUIDs for public IDs.

Centralize permission logic.

Do not rely only on frontend restrictions.

Backend must enforce organization isolation.

========================================
5. TESTS
========================================

Write automated tests for:

- user creation
- login
- token refresh
- current user
- organization creation
- membership creation
- role assignment
- duplicate membership prevention
- organization access
- unauthorized access
- cross-organization access

Create explicit IDOR tests.

Example:

User A belongs to Organization A.

User B belongs to Organization B.

User A must not be able to:

- retrieve Organization B
- modify Organization B
- access Organization B membership
- infer protected organization data through API responses

========================================
6. POSTMAN
========================================

Create/test requests for:

Register/create user
Login
Refresh token
Current user
Create organization
List organizations
Retrieve organization
Update organization

Use:

{{base_url}}

{{access_token}}

Configure Bearer authentication.

Verify unauthorized requests return appropriate errors.

========================================
7. FRONTEND
========================================

Build only:

- login page
- authentication state
- logout
- protected routes
- current-user loading
- organization context
- basic application shell

Do not build business modules.

Verify:

React → Django → PostgreSQL works.

========================================
8. FAILURE STATES
========================================

Test:

- invalid password
- invalid email
- expired token
- missing token
- malformed token
- missing organization
- unauthorized role
- duplicate organization membership
- cross-organization access

Frontend must display useful error states.

========================================
9. DATABASE INTEGRITY
========================================

Check using Django and DBeaver:

- users
- organizations
- memberships
- foreign keys
- unique constraints
- indexes
- orphaned records

Verify cascade/protection behavior is intentional.

========================================
10. SECURITY
========================================

Perform an explicit authorization review.

Check:

- password hashing
- JWT handling
- object-level permissions
- organization isolation
- IDOR
- mass assignment
- serializer exposure
- sensitive fields
- CORS
- token expiration

Never trust organization IDs supplied by the frontend.

========================================
11. GIT
========================================

Commit:

feat(backend): add authentication and organizations

Only commit after automated tests and Postman checks pass.

========================================
12. DOCUMENTATION
========================================

Document:

- authentication architecture
- role definitions
- organization isolation strategy
- permission strategy
- JWT approach
- important database constraints
- Postman workflow

Do not begin Stage 2 until Stage 1 is complete.