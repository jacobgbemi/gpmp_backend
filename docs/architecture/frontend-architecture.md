# GlintPM Private — Frontend Architecture

## Purpose
This document describes the intended React-based frontend architecture. Exact libraries and structure must be verified against the repository.

## Responsibilities
The frontend is responsible for:
- Presenting project information
- Collecting user input
- Managing client interaction state
- Calling backend APIs
- Displaying validation and error states
- Providing appropriate UX-level access visibility

The frontend is **not** the authoritative security layer.

## Conceptual Structure

```text
Pages / Routes
      ↓
Layouts
      ↓
Feature Components
      ↓
Reusable Components
      ↓
Hooks / State
      ↓
API Services
      ↓
Backend API
```

## Suggested Structure

```text
src/
├── app/
├── pages/
├── layouts/
├── components/
├── features/
├── hooks/
├── services/
├── api/
├── state/
├── types/
├── utils/
└── tests/
```

The actual repository structure takes precedence.

## State
Keep server state, UI state, form state, and authentication state conceptually separate. Avoid unnecessary duplication of server data.

## API Communication
Prefer centralized API services/hooks instead of scattering HTTP calls across presentation components.

## Forms
Important forms should handle loading, success, validation failure, authorization failure, network failure, and duplicate submission.

Server-side validation remains authoritative.

## Dashboards
Important project-control calculations should preferably be produced by authoritative backend logic rather than independently recalculated in multiple UI components.

## Accessibility
Important interfaces should support appropriate labels, keyboard navigation, focus management, and understandable errors.

## Testing
Test components, forms, API interactions, permissions, error states, and critical user journeys.

## Performance
Consider pagination, code splitting, lazy loading, efficient requests, and avoiding unnecessary re-renders. Optimize based on evidence.

## Verification Status
Exact frontend framework, libraries, state management, directory structure, and implementation patterns must be verified from the repository.
