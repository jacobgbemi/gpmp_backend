# AI Data Access

**Status:** AI data-access baseline  
**Last updated:** 2026-10-07

## Purpose

Define how AI should access project and organizational data safely.

## Core Rule

**AI access must never exceed the requesting user's existing authorization.**

If a user cannot access a project through the application, an AI feature must not provide that project's information either.

## Data Flow

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
Tenant / Organization Scope
 ↓
Data Query
 ↓
Context Filtering
 ↓
AI
```

## Minimum Necessary Context

Only provide information required for the task.

For example, a schedule-variance question may not require:

- unrelated projects;
- full employee records;
- private financial details;
- unrelated risk registers.

## Multi-Tenancy

AI retrieval must preserve organization/tenant boundaries.

Never use a global vector index or shared retrieval mechanism without enforcing tenant-level authorization.

## Sensitive Data

Sensitive project and personal information should be minimized before being sent to an external model provider where possible.

## Retrieval-Augmented Generation

If RAG is used:

- index only authorized content;
- attach tenant/project metadata;
- filter retrieval by authorization;
- preserve source references;
- prevent cross-tenant retrieval.

## Data Retention

Define whether prompts, retrieved context, and AI responses are:

- stored;
- temporarily processed;
- deleted;
- retained for audit.

Retention should follow security and privacy requirements.

## Data Provenance

AI-generated answers should identify their source data where practical, especially for important project decisions.
