# Logging

## Purpose
Provide useful operational and security diagnostics without exposing sensitive data.

## Levels
DEBUG for development diagnostics; INFO for normal events; WARNING for abnormal recoverable conditions; ERROR for failures; CRITICAL for severe impact.

## Structured fields
Use timestamp, severity, service, environment, request ID, safe user/organization reference, event type, and error category where appropriate.

## Never log
Passwords, tokens, session secrets, API keys, private keys, payment credentials, or unnecessary sensitive personal data.

Application logs support operations; security/business audit events should use the dedicated audit mechanism.
