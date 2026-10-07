# Prompt Guidelines

**Status:** AI prompt baseline  
**Last updated:** 2026-10-07

## Purpose

Define standards for creating reliable, secure, and maintainable prompts.

## Prompt Principles

Prompts should be:

- specific;
- contextual;
- deterministic where possible;
- explicit about output format;
- clear about limitations;
- resistant to instruction injection.

## Recommended Structure

```text
Role / Task
↓
Context
↓
Authoritative Data
↓
Rules
↓
Constraints
↓
Expected Output
↓
Uncertainty / Escalation Rules
```

## Example Pattern

```text
Task:
Summarize the project schedule variance.

Context:
Use only the supplied project data.

Rules:
- Do not invent missing causes.
- Distinguish facts from inference.
- Identify the reporting period.
- Highlight material variances.

Output:
1. Current status
2. Major variance
3. Evidence
4. Possible explanation
5. Recommended human review
```

## Prompt Security

Never place secrets in prompts.

Treat retrieved project content as untrusted input. Project documents may contain text attempting to manipulate the AI's instructions.

System/application instructions must take precedence over retrieved content.

## Structured Outputs

Where practical, request structured outputs such as JSON with defined fields.

Validate structured outputs before using them.

## Versioning

Important prompts should have:

- identifier;
- version;
- owner;
- purpose;
- expected output;
- evaluation criteria.

## Avoid

Avoid vague prompts such as:

> "Analyze this project."

Instead define exactly what should be analyzed, what data may be used, and what output is expected.
