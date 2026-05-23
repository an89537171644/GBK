# Validation Report

requires_engineer_review = true

## Verification Goal

Fix the current calculation core as a draft engineering MVP before dataset and
ML work. The goal is repeatable deterministic behavior, traceable intermediate
values, and explicit warnings where the MVP still has applicability limits.

## Checked Scope

- Rectangular bending check.
- Rectangular shear check.
- Draft transverse reinforcement counting conditions for Qsw.
- Longitudinal reinforcement selection.
- Transverse reinforcement selection.
- End-to-end rectangular design workflow.
- CLI paths for checks, selection, design, and dataset generation.

## Golden Cases

- `tests/golden_cases/bending_rectangular_case_01.md`
- `tests/golden_cases/bending_rectangular_case_02.md`
- `tests/golden_cases/shear_rectangular_case_01.md`
- `tests/golden_cases/design_rectangular_case_01.md`

## Covered Modules

- `sp63_core.checks.bending`
- `sp63_core.checks.shear`
- `sp63_core.rebar.longitudinal`
- `sp63_core.rebar.transverse`
- `sp63_core.rebar.constructive`
- `sp63_core.design.rectangular`
- `sp63_core.cli`

## Remaining Limits

- No cracks or deflections.
- No anchorage, bar curtailment, support zones, torsion, punching, columns, or T-sections.
- Material catalogs and constructive rules remain draft and require review.
- Golden cases are draft validation anchors, not final approval cases.

## Manual Engineering Review Needed

- Confirm formula cards against SP 63 source clauses.
- Confirm material tables and load-duration assumptions.
- Confirm constructive requirements and edge cases.
- Confirm selected reinforcement options against detailing practice.

## SCAD/LIRA Comparison Needed

- Compare bending capacities for representative B15-B40 and A400/A500 cases.
- Compare shear capacities and Qsw-counting warnings.
- Compare end-to-end selected reinforcement schemes for typical beams.

## Dataset Readiness

K7 adds a beam-only dataset MVP with expanded reinforcement, constructive, and
shear-rule fields. The generator rejects non-beam element types because slab
constructive requirements are not fully implemented in this MVP.

The dataset split and report utilities are ready for engineering review:

- deterministic train/validation/test split;
- CSV export for each split;
- JSON dataset report with ranges, class counts, split sizes, and
  `unsafe_rows_count`;
- expected `unsafe_rows_count = 0` for generated MVP rows.

The dataset remains draft data. It must be reviewed against engineering
expectations and representative external calculations before any ML baseline is
trained or interpreted as useful.

## K8 Dataset Generation Hardening

K8 strengthens dataset generation before any ML work:

- the stirrup diameter used in geometry and `h0` is forced to match the selected
  transverse reinforcement diameter;
- unsupported geometry stirrup diameters are rejected;
- dataset rows are generated from the full valid grid before applying `limit`;
- `limit` is applied after deterministic shuffle, controlled by `seed`;
- `group_key` is stored for leakage-safe train/validation/test splitting;
- dataset reports include group counts, duplicate case id counts, stirrup
  geometry mismatch counts, and selected reinforcement scheme counts.

No ML baseline should be started before reviewing the dataset report and the
draft golden cases manually.

## K9 Validation Package

K9 adds a programmable validation package:

- `run_bending_golden_cases()`;
- `run_shear_golden_cases()`;
- `run_design_golden_cases()`;
- `validate_dataset_cases()`;
- `build_scad_lira_comparison_template()`.

The CLI entry point is:

```bash
python -m sp63_core validate --golden
python -m sp63_core validate --generate-dataset-limit 100 --json
```

This package checks draft golden cases, validates generated datasets, and
prepares a manual SCAD/LIRA comparison table. It is a readiness step before ML,
not final certification.

## K10 External Engineering Validation

K10 adds external validation structures:

- `ExternalComparisonRow`;
- SCAD/LIRA CSV export from dataset program outputs;
- acceptance gate evaluation;
- JSON acceptance report export.

Acceptance is `warning` until external comparison rows are manually filled and
accepted by an engineer. The draft recommended maximum delta is 5%.

## K11 Strict External Acceptance

K11 closes the external validation loop:

- load a filled SCAD/LIRA comparison CSV;
- parse external numeric values and engineer acceptance flags;
- compute SCAD/LIRA deltas;
- export a CSV with delta fields;
- fail strict acceptance when external values are incomplete, rejected, or above
  the allowed delta.

The acceptance report now includes completed external row counts, incomplete row
counts, rejected row counts, and delta-exceeded row counts.

## K12 Baseline ML Sandbox

K12 adds an experimental baseline ML module for the beam-only strength dataset.
It extracts input-like features, trains RandomForest baselines, reports metrics,
and saves a model bundle for controlled experiments.

The ML sandbox is advisory only. It does not replace deterministic SP 63 checks,
golden validation, dataset validation, or external SCAD/LIRA acceptance gates.
The safety wrapper reruns the deterministic rectangular design workflow and
accepts an ML proposal only when the deterministic result is `pass`.

## K12.1 Leakage Removal And Proposal Safety

K12.1 removes `h0` from ML input features because it depends on selected
longitudinal bar diameter. `cover` is now stored in the dataset and used as an
input feature instead.

The ML safety path now reconstructs the predicted reinforcement scheme and runs
deterministic checks for that exact proposal. Safety metrics include
`deterministic_accept_rate` and `unsafe_prediction_rate`. ML remains
advisory-only regardless of these metrics.

## K12.2 Target Hygiene And Quality Gate

K12.2 removes `stirrup_diameter` from ML targets because
`geometry_stirrup_diameter` is an input geometry parameter and is equal to the
selected stirrup diameter in the current dataset MVP. This avoids target leakage
through the geometry input.

The baseline metrics now include target and feature counts, no longer include
`stirrup_diameter_accuracy`, and add `stirrup_legs_accuracy`. The ML quality
gate checks `As_MAPE`, `deterministic_accept_rate`, and
`unsafe_prediction_rate`. A pass is only a sandbox-quality result, not a design
approval.

## K13 Service Material Properties

K13 adds concrete service properties `Rbser` and `Rbtser` for heavy concrete
B15-B40. These values must be reviewed against SP 63 tables before future Mcrc
golden cases are created.

The K13 automated validation still covers the strength MVP only. Crack
formation, crack width, and deflection checks are not implemented in K13.

## K14 Normal Crack Formation Validation

K14 adds a draft golden case for normal crack formation in a rectangular beam:
B25 concrete, b = 300 mm, h = 500 mm, Mser = 30,000,000 N*mm. The expected
gross-section values are W = 12,500,000 mm3 and Mcrc = 19,375,000 N*mm.

This validation covers normal crack formation only. Crack width `acrc`,
deflection, transformed section behavior, long-term effects, prestress, axial
force, slabs, T-sections, and nonlinear deformation checks are still outside
the implemented scope.

## Conclusion

The core is a draft-MVP calculation kernel. It is suitable for controlled
engineering review and small validation datasets, but it is not a final
project-design calculation tool.
