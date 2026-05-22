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

## Conclusion

The core is a draft-MVP calculation kernel. It is suitable for controlled
engineering review and small validation datasets, but it is not a final
project-design calculation tool.
