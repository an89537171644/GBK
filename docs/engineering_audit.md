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
- K13 service concrete properties `Rbser` and `Rbtser` for future second
  limit-state preparation.
- K15 draft normal crack width `acrc` check for rectangular beams.
- K16 draft short-term curvature and deflection check for rectangular beams.
- K17 separated strength, serviceability, and overall protocol statuses.
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

- Long-term deflections and other refined serviceability checks beyond draft
  normal crack formation, draft normal crack width, and draft short-term
  deflection.
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

K8 makes the dataset pipeline more stable, but it still does not cover
serviceability data, deflections, T-sections, columns, slabs, punching, torsion,
anchorage, support zones, or bar curtailment. ML may begin only after reviewing
`dataset_report` outputs and manually checking the draft golden cases.

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

## K13 Service Concrete Properties

K13 adds `Rbser` and `Rbtser` to the heavy concrete B15-B40 draft catalog. These
properties prepare the core for future second limit-state checks such as normal
crack formation and deflection calculations.

Crack checks and deflection checks are not implemented in K13. ML is not trained
on serviceability data, and the K13 validation still covers the strength MVP
only.

## K14 Normal Crack Formation

K14 adds the first draft serviceability check: normal crack formation `Mcrc` for
rectangular reinforced concrete beams. The implementation uses `Rbtser` and a
gross elastic concrete section.

This is not a crack width or deflection check. It does not include transformed
section behavior, long-term effects, axial force, prestress, slabs, T-sections,
or nonlinear deformation modeling. The result is a draft-MVP signal that crack
width `acrc` must be checked in a later deterministic step when normal cracks
are expected.

## K15 Normal Crack Width

K15 adds a draft normal crack width `acrc` check for rectangular reinforced
concrete beams. The implementation uses service reinforcement property `Rsser`,
a simplified elastic cracked reinforcement stress estimate, and bounded draft
crack spacing.

This is not a refined SP 63 crack width model. It does not include refined crack
spacing, tension stiffening, long-term effects, transformed-section behavior,
or nonlinear deformation modeling. Deflection is still not implemented. ML
modules were not changed and ML remains advisory-only.

## K16 Curvature And Deflection

K16 adds a draft short-term curvature and deflection check for rectangular
reinforced concrete beams. The implementation uses K14 crack formation to
select gross uncracked stiffness or a simplified cracked transformed stiffness
without tensile concrete.

This is not a refined SP 63 deformation model. It does not include long-term
deflection, creep, shrinkage, refined tension stiffening, nonlinear deformation,
slabs, columns, T-sections, punching, torsion, anchorage, support zones, bar
curtailment, or Streamlit. ML modules were not changed and ML remains
advisory-only.

## K17 Status Separation

K17 separates calculation protocol statuses into `strength_status`,
`serviceability_status`, and `overall_status`. Strength status is based only on
bending and shear. Serviceability status is based on crack formation, crack
width, and deflection. The legacy `status` field remains as an alias for
`overall_status`.

This change does not alter bending, shear, crack formation, crack width, or
deflection formulas. It makes serviceability failures visible in the final
design status instead of allowing a passed strength result to mask them. ML
modules were not changed and ML remains advisory-only.

## K19 Material Catalog Audit

K19 adds a transparent audit layer for the concrete and reinforcement catalogs.
The audit report lists current draft values, their usage in strength or
serviceability checks, units, and review flags.

All material values remain `draft_requires_engineer_review`. The audit does not
approve normative values and does not store full SP 63 text. An engineer must
verify concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb` and reinforcement `Rsn`,
`Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es` against the applicable
tables before final use.

K19 does not change calculation formulas, ML modules, dataset generation, or
external validation gates. ML remains advisory-only and deterministic SP 63
checks remain mandatory.

## K20 Manual SP63 Verification Cases

K20 adds six manual verification cases as a repeatable check against the
deterministic draft calculation core. The cases cover a passing beam, bending
failure, crack-formation review without crack width, crack-width failure,
deflection failure, and shear failure.

The verification package compares program values with manual expected values
using documented tolerances and checks separated `strength_status`,
`serviceability_status`, and `overall_status` values.

K20 does not change calculation formulas, material values, ML modules, dataset
generation, or external validation. The cases are draft verification material
and still require engineer review.

## K21 Dataset Enrichment

K21 enriches the beam-only dataset with deterministic strength and draft
serviceability outputs from the calculation core. Rows now expose selected
reinforcement areas, bending and shear capacities, Mcrc, crack width,
deflection, separated strength/serviceability/overall statuses, warning counts,
review flags, and an `unsafe_row` marker.

This improves ML-readiness diagnostics, but it does not approve the dataset for
final design use. The generated values still depend on draft serviceability
checks and material catalogs that require engineer review. ML remains
advisory-only and every ML proposal must continue to pass deterministic checks.

## K22 ML Readiness Gate

K22 adds an ML readiness report for enriched deterministic datasets. The report
checks required columns, unsafe row counts, status distributions, group leakage,
and constant target/status columns before any later ML work.

This is a gate, not training. A safe accepted dataset with only passing rows is
useful, but it is not sufficient for classification over pass/fail/review
statuses. Fail and review diagnostic cases must be added deliberately in a
future dataset step before classification ML. ML remains advisory-only and
deterministic SP63 checks remain mandatory.

## K23 Diagnostic Dataset

K23 adds that separate diagnostic/candidate dataset. It intentionally contains
passing, failing, and review-required rows generated through deterministic
checks. The safe accepted dataset remains unchanged and should still be used for
accepted-row regression experiments.

The diagnostic dataset is not a project-design dataset. It exists to make
future classification ML development possible after engineer review. Rows with
failure and review statuses must not be interpreted as approved reinforcement
solutions. ML remains advisory-only.

## K24 Baseline ML Without Neural Network

K24 adds a non-neural baseline ML report for engineering review of dataset
readiness. It uses simple sklearn baselines for regression on the safe accepted
dataset and classification of `overall_status` on the diagnostic dataset.

The report does not make ML a calculator and does not train a neural network.
It explicitly records that ML is advisory-only and deterministic SP63 checks
remain mandatory. The diagnostic dataset is intentionally small, so
classification metrics are smoke metrics rather than evidence of production ML
quality.

## Next Stages

- Engineer review of material catalogs and formula cards.
- Engineer review of constructive checks.
- Dataset split and validation policy.
- Golden-case expansion.
- Baseline ML review only after deterministic checks and external validation
  gates are accepted.
