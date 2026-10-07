# AI Human Oversight

**Status:** AI governance baseline  
**Last updated:** 2026-10-07

## Purpose

Define where human judgment must remain in control of AI-assisted project-controls workflows.

## Core Principle

AI can assist with analysis and preparation, but accountability for consequential project decisions remains with authorized people.

## Human-in-the-Loop

Human review should be required for material actions involving:

- baseline approval;
- budget approval;
- financial commitments;
- contractual changes;
- schedule recovery commitments;
- major forecast decisions;
- risk acceptance;
- external reporting.

## Human-on-the-Loop

For lower-risk automation, users may supervise outcomes through:

- monitoring;
- exception alerts;
- sampling;
- audit logs;
- periodic review.

## Approval Pattern

```text
AI Suggestion
     ↓
Evidence / Sources
     ↓
Human Review
     ↓
Approve / Edit / Reject
     ↓
Controlled Application Action
```

## Explainability

Where practical, users should be able to understand:

- what data informed the recommendation;
- what the AI concluded;
- what assumptions were made;
- what uncertainty exists.

## Override

Users with appropriate authority should be able to reject or correct AI output.

AI recommendations must not make it difficult for users to exercise professional judgment.

## Accountability

The system should distinguish between:

- AI-generated suggestion;
- user-edited content;
- approved decision;
- automated calculation.

## Escalation

AI should escalate when:

- required information is missing;
- evidence conflicts;
- confidence is low;
- the requested action is outside its authority;
- the decision has significant financial, contractual, safety, or project impact.

## Governance

AI capabilities should have an identified owner responsible for:

- evaluation;
- monitoring;
- prompt/model changes;
- security review;
- incident handling;
- periodic reassessment.
