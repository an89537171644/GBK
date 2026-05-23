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

## Conclusion

The core is a draft-MVP calculation kernel. It is suitable for controlled
engineering review and small validation datasets, but it is not a final
project-design calculation tool.
