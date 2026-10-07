# GlintPM Private — Authorization

## Purpose
Authorization controls what an authenticated identity may access or modify.

## Core Rule
Frontend visibility is not a security boundary. Backend authorization must enforce permissions.

## Conceptual Model

```text
User → Organization Membership → Role → Project Access → Action Permission
```

## Potential Roles
- Organization Administrator
- Project Director
- Project Manager
- Project Controls Manager
- Planner
- Cost Engineer
- Project Team Member
- Executive / Viewer

Actual roles must be derived from requirements and implementation.

## Potential Permissions
- View
- Create
- Update
- Archive/delete
- Approve
- Export
- Manage users
- Manage permissions
- Establish baseline
- Approve changes
- Access financial information

## Object-Level Authorization
Verify both action permission and access to the specific object.

```text
User A → Can edit projects? YES → Can edit Project 123? NO → Deny
```

## Organization Isolation
For multi-organization operation, project/resource access must be scoped server-side to the user's organization memberships.

## State-Based Authorization
Some actions may depend on lifecycle state.

```text
Draft → Submitted → Approved
```

For example, an approved baseline may require a controlled revision process rather than ordinary editing.

## Privileged Actions
Give additional controls to high-impact operations such as baseline approval, change approval, permission changes, deletion/restoration, and sensitive exports.

## Testing
Test allowed/denied users, wrong organizations, wrong projects, wrong roles, invalid states, privileged operations, and direct API bypass attempts.

## Verification Status
Actual roles, permissions, policy logic, middleware, and object-level controls must be verified against the implementation.
