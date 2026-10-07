# Costs API

- **Status:** API documentation baseline
- **Date:** 2026-10-05

## Purpose

The Costs API manages budgets, commitments, actuals, forecasts, and cost variance where supported.

## Conceptual endpoints

```text
GET  /api/projects/{project_id}/costs/
POST /api/projects/{project_id}/costs/
GET  /api/costs/{cost_id}/
PATCH /api/costs/{cost_id}/
GET  /api/projects/{project_id}/costs/summary/
```

## Cost record

```json
{"id":"cost-id","project_id":"project-id","cost_type":"actual","amount":"1250000.00","currency":"USD","period":"2026-09","status":"approved"}
```

Monetary values should use exact numeric representations rather than floating-point values.

## Cost types

Potential categories include budget, committed, actual, forecast, estimate, accrual, and variance. Supported categories must be defined by the domain model.

## Currency

Currency must be explicit where multiple currencies can coexist. Do not assume a universal currency unless the product enforces one.

## Summary

A summary may expose budget, actual, commitment, forecast, and variance. Each metric must have a documented formula before becoming an authoritative KPI.

## Validation

Validate amount, currency, cost type, project access, reporting period, and lifecycle restrictions on approved records.

## Authorization and audit

Financial information should have explicit permissions. Important budget, actual, forecast, and approval changes should be auditable.

## Common errors

`400` invalid financial data, `401` authentication, `403` financial access denied, `404` unavailable resource, `409` conflicting approved state.
