# Troubleshooting

## Workflow
`Observe → Reproduce → Check recent changes → Inspect logs/metrics → Identify layer → Test hypothesis → Controlled fix → Verify → Document`

## Layers
Frontend: browser console, network requests, auth state, build/version.

API: endpoint, status, request ID, authentication, authorization, validation.

Backend: exceptions, configuration, dependencies, database connectivity, recent releases.

Database: connectivity, migrations, constraints, locks, query performance, storage.

## Common HTTP checks
401 = authentication; 403 = authorization; 404 = route/resource/scope; 400/422 = validation; 409 = conflict; 429 = rate limit; 500 = server failure.

Never expose secrets, permanently disable security controls, or make destructive production changes without authorization and recovery planning.
