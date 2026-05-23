# Engineering Audit

requires_engineer_review = true

## Implemented

- Draft material catalogs for heavy concrete B15-B40 and reinforcement A240/A400/A500.
- Rectangular section geometry with effective depth handling.
- Draft bending check for rectangular sections.
- Draft shear check for rectangular sections.
- Longitudinal reinforcement selection with layout and constructive filters.
- Transverse reinforcement selection with shear and constructive filters.
- K7 draft warnings for conditions of counting transverse reinforcement in shear.
- K8 hardened dataset generation with consistent stirrup geometry, deterministic
  shuffled limits, group split, and extended dataset reports.
- K9 validation package for draft golden cases, dataset checks, and SCAD/LIRA
  comparison template.
- K10 external validation structures and acceptance gates for manual SCAD/LIRA
  review.
- K11 strict loading of filled SCAD/LIRA comparisons, delta export, and strict
  acceptance report.
- K12 experimental baseline ML sandbox for beam-only strength dataset.
- K12.1 leakage removal and deterministic safety checks for reconstructed ML
  reinforcement proposals.
- K12.2 target hygiene removing `stirrup_diameter` prediction and adding an ML
  sandbox quality gate.
- End-to-end rectangular element design workflow.
- CLI scenarios for checks, selection, design, and dataset generation.

## Applicability Boundaries

- Rectangular bending elements only.
- Heavy concrete and MVP reinforcement classes only.
- Units follow the project convention: N, mm, MPa.
- Results are draft engineering outputs and require review before production use.

## Requires Engineering Review

- Material values and load-duration assumptions.
- Bending and shear formula cards and golden cases.
- Constructive limits and edge cases.
- Reinforcement layout assumptions.
- Dataset ranges before bulk generation.
- Dataset reports, group split behavior, and golden cases before ML work.
- K9 validation reports before any baseline ML training.
- External SCAD/LIRA comparison rows and acceptance gates before ML is treated
  as more than experimental.
- Filled external CSV with strict pass status before baseline ML proceeds beyond
  an experimental sandbox.

## Not Implemented

- Serviceability limit states, including cracks and deflections.
- T-sections, columns, punching, torsion, prestress, anchorage, support zones,
  and bar curtailment.
- HTML/PDF protocol rendering.
- Production ML-backed recommendations.
- Streamlit or other UI.

## Why ML Is Not A Final Calculation Stage Yet

The deterministic calculation core is still draft and requires engineering review.
ML can only be used after the calculation rules, constructive filters, datasets,
and validation cases are reviewed. Even then, ML output must remain advisory and
must be checked by deterministic SP 63 calculation modules.

K7 strengthens the shear check by reporting draft Qsw-counting conditions. This
does not make ML acceptable as a final stage; deterministic checks and manual
engineering review are still required.

K8 makes the dataset pipeline more stable, but it still does not cover cracks,
deflections, T-sections, columns, slabs, punching, torsion, anchorage, support
zones, or bar curtailment. ML may begin only after reviewing `dataset_report`
outputs and manually checking the draft golden cases.

K9 adds automated validation summaries, but this is not certification. The
outputs still require manual engineering review and external comparison.

K10 adds acceptance gates. A `warning` result means external comparison has not
been filled yet; this blocks treating ML as engineering-ready.

K11 requires completed external values and engineer acceptance flags for strict
`pass`. Missing values, rejected rows, or excessive deltas fail acceptance.

K12 introduces a baseline ML sandbox only after the validation-gate structure is
in place. The sandbox is experimental and advisory. It must not be used as a
final calculation stage, and every prediction must be checked by deterministic
SP 63 modules.

K12.1 removes `h0` from ML input features because it leaks selected bar diameter
information. It adds `cover` as the geometry input and checks the reconstructed
ML reinforcement proposal itself through deterministic layout, constructive,
bending, and shear checks. `unsafe_prediction_rate` must be monitored before
any ML use beyond sandbox experiments.

K12.2 treats `geometry_stirrup_diameter` as an input geometry parameter and
removes `stirrup_diameter` from ML targets because they are equal in the current
dataset MVP. The ML quality gate monitors `As_MAPE`,
`deterministic_accept_rate`, and `unsafe_prediction_rate`, but even a passing
gate leaves ML advisory-only.

## Next Stages

- Engineer review of material catalogs and formula cards.
- Engineer review of constructive checks.
- Dataset split and validation policy.
- Golden-case expansion.
- Baseline ML review only after deterministic checks and external validation
  gates are accepted.
