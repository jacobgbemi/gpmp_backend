# AI Security

**Status:** AI security baseline  
**Last updated:** 2026-10-07

## Purpose

Define security controls specific to AI-enabled features.

## Primary Threats

Consider:

- prompt injection;
- data leakage;
- cross-tenant retrieval;
- excessive model permissions;
- malicious documents;
- insecure tool use;
- model hallucination;
- sensitive information exposure;
- compromised AI provider credentials.

## Prompt Injection

Treat all external/retrieved content as untrusted.

A project document containing instructions such as "ignore previous instructions" must not override application-level instructions.

## Least Privilege

AI tools should receive only the permissions necessary for their task.

Prefer:

```text
Read-only schedule analysis
```

over:

```text
Full database access
```

## Tool Actions

If AI can call application tools, separate:

- read operations;
- analysis operations;
- write operations;
- approval operations.

High-impact writes should require explicit user confirmation.

## Secrets

AI providers' API keys must be stored using secure secret-management mechanisms and never embedded in prompts or frontend code.

## Tenant Isolation

Every AI data-access path must enforce tenant and project authorization.

## Output Safety

Do not blindly execute model-generated:

- SQL;
- shell commands;
- code;
- URLs;
- API requests;
- database mutations.

Validate and constrain all tool calls.

## Logging

Log sufficient metadata for security investigation without storing unnecessary sensitive prompt/response content.

## Security Testing

AI features should be tested against:

- prompt injection;
- unauthorized data access;
- malicious documents;
- tool abuse;
- output manipulation;
- tenant-boundary violations.
