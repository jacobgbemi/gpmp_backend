# Disaster Recovery

## Purpose
Define recovery from major service or infrastructure failure.

## Scenarios
Database corruption, accidental deletion, provider outage, compromised credentials, failed deployment, infrastructure loss, ransomware, or loss of critical configuration.

## Objectives
Define RPO (maximum tolerable data loss) and RTO (maximum tolerable recovery time) according to business requirements.

## Recovery
`Detect → Assess → Contain → Declare → Restore infrastructure/data → Deploy known-good version → Verify integrity → Restore service → Monitor`

For security incidents, preserve evidence, rotate compromised credentials, review access, and meet applicable notification obligations.

Recovery exercises should record actual RTO/RPO and improvement actions.
