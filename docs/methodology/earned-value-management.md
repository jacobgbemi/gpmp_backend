# Earned Value Management

**Status:** Methodology baseline  
**Last updated:** 2026-10-07

## Purpose

Earned Value Management (EVM) integrates scope, schedule, and cost information to assess project performance.

## Core Terms

### Planned Value (PV)

Budgeted value of work planned to be performed by the data date.

### Earned Value (EV)

Budgeted value of work actually performed by the data date.

### Actual Cost (AC)

Actual cost incurred for the work performed by the data date.

## Core Variances

```text
Schedule Variance (SV) = EV − PV

Cost Variance (CV) = EV − AC
```

## Performance Indices

```text
Schedule Performance Index (SPI) = EV / PV

Cost Performance Index (CPI) = EV / AC
```

Interpretation commonly follows:

- CPI > 1: favorable cost efficiency;
- CPI < 1: unfavorable cost efficiency;
- SPI > 1: progress is ahead of the PV curve;
- SPI < 1: progress is behind the PV curve.

The project control procedure should define the approved interpretation and measurement rules.

## Forecasting

Common EVM forecast concepts include:

```text
EAC = BAC / CPI
```

or other formulas depending on assumptions.

Where:

- BAC = Budget at Completion
- EAC = Estimate at Completion

EVM calculations should not be treated as universally valid without understanding the assumptions behind the chosen formula.

## Data Quality

EVM depends on reliable:

- baseline budget;
- progress measurement;
- actual cost;
- data date;
- coding structure.

## Important Limitation

Schedule Variance in traditional EVM is expressed in value terms, not calendar days. Time-based schedule analysis should complement EVM rather than be replaced by it.
