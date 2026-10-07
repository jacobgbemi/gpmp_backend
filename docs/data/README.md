# Data Documentation

This directory contains conceptual and architectural data documentation for GlintPM Private.

| Document | Purpose |
|---|---|
| [data-model.md](data-model.md) | Core entities and ownership model |
| [entity-relationship.md](entity-relationship.md) | Conceptual entity relationships |
| [data-dictionary.md](data-dictionary.md) | Meaning of major data elements |
| [data-validation.md](data-validation.md) | Validation rules and validation layers |
| [data-integrity.md](data-integrity.md) | Integrity, consistency, transactions, and constraints |
| [data-lifecycle.md](data-lifecycle.md) | Creation, state changes, archival, retention, and deletion |
| [audit-trail.md](audit-trail.md) | Data-level audit requirements |
| [data-import-export.md](data-import-export.md) | Import/export lifecycle and controls |
| [reporting-data-model.md](reporting-data-model.md) | Reporting facts, dimensions, snapshots, and KPIs |

These documents define intended data architecture and are not proof of implementation. Django models, migrations, serializers, services, tests, database configuration, and reporting code remain the implementation source of truth.

When the physical schema changes materially, update the relevant documentation and record significant architectural changes in `/docs/decisions/`.
