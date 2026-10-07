# AI Evaluation

**Status:** AI evaluation baseline  
**Last updated:** 2026-10-07

## Purpose

Define how AI features should be evaluated before and after release.

## Evaluation Dimensions

Measure:

- factual accuracy;
- relevance;
- completeness;
- consistency;
- groundedness;
- safety;
- authorization correctness;
- latency;
- cost;
- user usefulness.

## Test Dataset

Maintain representative evaluation cases covering:

- normal inputs;
- incomplete inputs;
- ambiguous requests;
- incorrect data;
- edge cases;
- malicious prompts;
- cross-tenant access attempts.

## Groundedness

For project-specific answers, verify that claims are supported by authorized source data.

A model should not be rewarded for confidently inventing an explanation when the data does not support one.

## Evaluation Example

| Test | Expected |
|---|---|
| Schedule variance summary | Uses supplied values |
| Missing cause | States that cause is unknown |
| Unauthorized project request | Refuses access |
| Conflicting data | Identifies conflict |
| Prompt injection | Ignores malicious instruction |

## Human Evaluation

For important features, qualified users should review outputs for:

- correctness;
- usefulness;
- clarity;
- project-controls validity.

## Regression Testing

Maintain a fixed evaluation set and rerun it after:

- model changes;
- prompt changes;
- retrieval changes;
- data-schema changes;
- tool changes.

## Release Gate

High-impact AI functionality should not be released solely because it produces plausible answers. It should meet predefined accuracy, safety, and authorization thresholds.
