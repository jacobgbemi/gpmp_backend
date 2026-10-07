# API Testing

**Status:** Testing baseline

## Purpose

API tests verify HTTP contracts and ensure clients receive predictable responses for valid, invalid, unauthorized, and forbidden requests.

## Coverage Areas

Each important endpoint should be tested for:

- HTTP method behavior.
- Authentication requirements.
- Authorization.
- Request validation.
- Successful responses.
- Error responses.
- Resource ownership/tenant scope.
- Pagination and filtering.
- Idempotency where applicable.
- Serialization format.
- Status codes.

## Core Scenarios

```text
Unauthenticated request → 401
Authenticated without permission → 403
Invalid input → 400/422 as defined by API contract
Missing resource → 404
Conflict → 409 where applicable
Successful creation → 201
Successful retrieval/update → 200
Successful deletion → 204 where applicable
```

The exact status code should follow the API contract rather than being assumed from this example.

## Security Cases

API tests should attempt to access another organization's resources using guessed, modified, or copied identifiers. The request must not disclose unauthorized information.

## Contract Stability

Changes to response fields, required inputs, error structures, or status codes should be treated as API contract changes and reviewed accordingly.

## Implementation Note

The actual API test framework, endpoint names, authentication mechanism, and response contracts must be verified from the repository.
