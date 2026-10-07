# Data Import and Export

- **Status:** Architectural baseline
- **Date:** 2026-10-05

## Purpose

GlintPM Private may exchange project-controls information with external tools and file formats. Imports and exports must preserve data quality, tenant isolation, traceability, and business meaning.

## Potential sources

Potential sources include Primavera P6, Microsoft Project, Excel/CSV, ERP/accounting systems, other project systems, and approved APIs. Actual supported integrations must be verified.

## Import lifecycle

```text
Upload / Receive
      ↓
Identify Tenant
      ↓
Parse
      ↓
Validate Structure
      ↓
Validate Business Rules
      ↓
Map Fields
      ↓
Preview / Review
      ↓
Commit
      ↓
Audit
```

## File validation

Validate format, size, encoding, required fields, types, duplicates, references, dates, numeric values, tenant context, and security.

## Mapping

Define external-to-internal field mappings. Mapping rules should be version-controlled where repeatability matters.

## Idempotency

Repeated imports should not create unintended duplicates. Use stable external identifiers, import batches, hashes, or another suitable strategy.

## Errors

Report errors at record/field level where practical, e.g.:

```text
Row 42
Activity Code: A-104
Error: Finish date precedes start date
```

## Transactions

Validated imports should be committed atomically where practical. Large imports may use controlled batches with explicit status and recovery behavior.

## Provenance

Imported records should retain useful source information such as source system, import batch, external identifier, import timestamp, and importing user/system.

## Exports

Exports must respect authorization and tenant isolation, identify relevant data date/reporting period, avoid secrets, and audit sensitive exports.

## Conflict handling

Define whether conflicts are rejected, overwritten, merged, versioned, or sent for review. Never silently overwrite authoritative project-control information without an explicit rule.

## Security

Uploaded and exported data may contain sensitive business information. Apply authorization, file restrictions, secure temporary storage, controlled access, and retention/deletion policies.
