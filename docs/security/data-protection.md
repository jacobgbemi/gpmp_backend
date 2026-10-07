# Data Protection

**Status:** Security baseline
**Last updated:** 2026-10-06

## Purpose

Define safeguards for project and user data throughout its lifecycle.

## Data classification

A practical classification model is:

| Class | Examples | Baseline handling |
|---|---|---|
| Public | Published marketing content | Integrity protection |
| Internal | Non-public operational information | Authenticated access |
| Confidential | Project, commercial, cost, schedule data | Least privilege + protected transport/storage |
| Restricted | Credentials, secrets, sensitive security data | Strong access control + dedicated secret handling |

## Data in transit

Production application traffic should use HTTPS/TLS. Internal service connections should also use protected transport where the environment and risk require it.

## Data at rest

Database, backup, object storage, and other persistent systems should use appropriate access controls and encryption capabilities based on sensitivity and infrastructure support.

## Data integrity

Protect integrity through:

- Database constraints.
- Server-side validation.
- Transaction boundaries.
- Controlled state transitions.
- Audit records for important changes.
- Backup and restore procedures.

## Data minimization

Collect and retain only information required for product functionality, security, legal obligations, or clearly defined business purposes.

## Export protection

Reports and exports can create a secondary copy of sensitive information. Export functionality should therefore:

- Require authorization.
- Limit the data to what the user is permitted to access.
- Apply appropriate file and response handling.
- Be auditable for sensitive or privileged exports.

## Retention and deletion

Retention periods should be defined by data type and business/legal requirements. Deletion must consider dependent records, audit requirements, backups, and regulatory obligations.

## Backups

Backups should be:

- Access-controlled.
- Protected from accidental deletion where practical.
- Tested through restoration exercises.
- Stored separately enough to reduce the impact of a primary-system compromise.

## Implementation note

Actual encryption settings, retention periods, backup providers, and deletion workflows must be verified from the deployed system before being described as implemented.
