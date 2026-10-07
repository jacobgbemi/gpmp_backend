# Environment Setup

## Purpose
Define consistent development, test, staging, and production environments.

## Environments
| Environment | Purpose |
|---|---|
| Development | Local development |
| Test/CI | Automated verification |
| Staging | Production-like validation |
| Production | Live workload |

## Configuration
Separate database credentials, Django settings, allowed hosts, CORS/CSRF, authentication, email, storage, logging, integrations, and secrets from source code.

## Local setup
1. Clone repository.
2. Create isolated Python environment.
3. Install backend dependencies.
4. Install frontend dependencies.
5. Configure local variables.
6. Configure PostgreSQL/development database.
7. Run migrations.
8. Start backend and frontend.
9. Run tests.

Production secrets must never be committed or reused in development.
