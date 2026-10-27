# Report field guide

| Field | Meaning |
|---|---|
| `UDI`, `ProductID` | Source row ID and product ID; each row is one synthetic cycle |
| `Type`, `TypeName` | L/M/H product quality variant and readable name |
| `AirTempK`, `ProcessTempK`, `ThermalGapK` | Temperatures in Kelvin and process-minus-air difference |
| `SpeedRPM`, `TorqueNm`, `ToolWearMin` | Operating measurements |
| `MechanicalPowerW` | Calculated torque × speed × 2π/60, watts |
| `WearBand`, `PowerBand` | Ordered display bands from the measurements |
| `Failure` | Source overall machine-failure label, 0/1 |
| `TWF`, `HDF`, `PWF`, `OSF`, `RNF` | Five unmodified source failure-mode flags |
| `PrimaryMode` | Mutually exclusive display bucket for failed rows; `No failure` otherwise |
| `ModeFlagCount` | Sum of the five raw mode flags |
| `LabelMismatch` | 1 if overall label differs from any-mode flag |
| `CycleCount` | Constant 1 for count and rate denominators |
| `SequenceBlock`, `SequenceBlockLabel` | 500-row UDI blocks, not calendar periods |

The report uses `SUM(events[CycleCount])`, `SUM(events[Failure])`, and `SUM(events[LabelMismatch])` for its KPI cards. Its product-variant and wear charts use `AVERAGE(events[Failure])` as a 0–1 failure-rate fraction. The mode donut uses `PrimaryMode` and `SUM(events[Failure])`, so nonfailed rows contribute zero. The interactive Power BI pages support tooltips and visual selection. A future model refinement could add a formatted DAX `Failure Rate = DIVIDE(SUM(events[Failure]), SUM(events[CycleCount]))` measure and a product-variant slicer on the KPI page.
