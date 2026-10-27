# Findings and interpretation

The overall failure label marks **339 of 10,000** synthetic cycle records (3.39%). Counts use `Failure`; rates divide `sum(Failure)` by `sum(CycleCount)` within the selected filter context. Product variant and wear-band totals reconcile to 10,000 rows.

| Product variant | Cycles | Failures | Rate |
|---|---:|---:|---:|
| Low | 6,000 | 235 | 3.92% |
| Medium | 2,997 | 83 | 2.77% |
| High | 1,003 | 21 | 2.09% |

Tool wear of **200+ minutes** has 123 failures in 801 records (15.36%). This is an association in a rule-generated dataset; the report does not estimate a treatment effect or suggest a replacement interval.

Mechanical power is calculated as torque × rotational speed × 2π/60. In the prepared data, the below-3.5 kW band contains 31 failures in 31 records, the above-9 kW band 64 in 64, and the middle band 244 in 9,905 (2.46%). The source generation includes power-based failure rules; the extreme-band result is therefore expected and unsuitable as independent model-validation evidence.

Among the 339 failed records, mutually exclusive display categories are: heat dissipation failure (HDF) 106, power failure (PWF) 80, overstrain failure (OSF) 78, tool wear failure (TWF) 42, multiple mode flags 24, and no specified mode 9. `PrimaryMode` is for display only. Raw flags are retained separately.

## Source-label audit

The overall failure label and the OR of all five mode flags disagree on **27 records**: 9 failed records have no flag, and 18 nonfailed records have at least one flag. A further 24 failed records have multiple flags. No labels were altered to force agreement. Report filters should use `Failure` for the top-line KPI, and mode charts should explicitly filter `Failure = 1` or use `PrimaryMode` as documented.

## Scope

- The data is **synthetic**, with no real failure dates, downtime durations, repair costs, or machine-level asset IDs.
- `UDI` and `SequenceBlock` are record order only. They are not dates, shifts, or time at risk.
- Product `Type` denotes product quality variants (L/M/H), not equipment classes.
- All rates describe this provided dataset. There is no training/test split, predictive model, or claim of operational generalization.
