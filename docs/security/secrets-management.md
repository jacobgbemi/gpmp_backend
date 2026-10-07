# Secrets Management

**Status:** Security baseline
**Last updated:** 2026-10-06

## Purpose

Define how credentials, API keys, signing keys, database passwords, and other secrets are handled.

## Secrets include

- Database credentials.
- Django secret/signing keys.
- API credentials.
- Third-party service tokens.
- Cloud or infrastructure credentials.
- Encryption keys.
- CI/CD credentials.

## Rules

1. Never commit secrets to Git.
2. Never place secrets in frontend source code or browser-visible configuration.
3. Never log secret values.
4. Use environment variables or an approved secrets manager for runtime configuration.
5. Restrict access to secrets using least privilege.
6. Rotate secrets after suspected exposure.
7. Use separate credentials for development, testing, staging, and production.
8. Remove unused credentials promptly.

## Environment separation

```text
Development secrets  !=  Test secrets  !=  Staging secrets  !=  Production secrets
```

A production credential should never be required to run the normal local development environment.

## Rotation

Rotation should be supported for high-impact credentials and performed when:

- A secret is exposed.
- A team member with access leaves or changes responsibilities.
- A vendor or integration requires rotation.
- A credential reaches its defined maximum lifetime.
- Incident investigation indicates possible compromise.

## Secret exposure response

If a secret is committed or otherwise exposed:

1. Revoke or rotate it immediately.
2. Identify where it was used.
3. Review logs and access activity.
4. Remove the secret from active source/configuration where appropriate.
5. Assess whether historical repository copies or artifacts remain accessible.
6. Document the incident and corrective actions.

## Implementation note

The exact production secret store, CI/CD secret configuration, and environment-variable names must be documented only after verifying the deployment implementation.
