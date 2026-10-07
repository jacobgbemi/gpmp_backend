# AI Architecture

**Status:** AI architecture baseline  
**Last updated:** 2026-10-07

## Purpose

Define a conceptual architecture for safely integrating AI into GlintPM Private.

## Conceptual Architecture

```text
User
  ↓
React Frontend
  ↓
Django API
  ↓
AI Orchestration Layer
  ├── Authorization
  ├── Context Selection
  ├── Prompt Construction
  ├── Model Provider
  ├── Output Validation
  └── Audit / Observability
          ↓
Project Data / Knowledge Sources
```

## Core Principle

The model should not receive unrestricted database access.

The application should determine:

1. who the user is;
2. what organization they belong to;
3. what data they may access;
4. what context is relevant;
5. what operation is permitted.

## AI Request Lifecycle

```text
User Request
   ↓
Authenticate
   ↓
Authorize
   ↓
Retrieve Allowed Context
   ↓
Construct Prompt
   ↓
Call Model
   ↓
Validate Output
   ↓
Present to User
   ↓
Optional Human Approval
```

## Model Provider

The architecture should allow the model provider to be changed without coupling business logic directly to a single provider.

## Deterministic Logic

Calculations such as:

- cost totals;
- EVM formulas;
- schedule metrics;
- permissions;
- validation;

should preferably be performed by application logic rather than relying on model-generated arithmetic.

## Failure Handling

AI failures should not make core project-controls workflows unavailable.

The application should handle:

- provider timeout;
- provider error;
- invalid model output;
- rate limits;
- unavailable model;
- context retrieval failure.

## Auditability

AI interactions that materially affect business workflows should be auditable without unnecessarily storing sensitive prompts or responses.
