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

## K25 Expanded Diagnostic Dataset

K25 expands the diagnostic/candidate dataset while keeping the safe accepted
dataset separate. The diagnostic set now includes generated deterministic rows
for pass, bending failure, shear failure, crack-width failure, deflection
failure, crack-review, and multiple-failure scenarios.

This improves classification readiness diagnostics, but it does not create a
design dataset and does not approve any failing or review-required rows as
solutions. Every diagnostic row still requires engineer review. ML remains
advisory-only and deterministic SP63 checks remain mandatory.

## K26 Baseline ML Evaluation on Expanded Diagnostic Dataset

K26 extends the non-neural baseline report to evaluate `overall_status`
classification on the expanded K25 diagnostic dataset with a fixed train/test
split. The report includes accuracy, macro F1, per-class precision and recall,
confusion matrix, and class distribution.

The report separates `input_only_features` from
`deterministic_derived_features`. The derived feature mode is review-only
because deterministic outputs such as capacities, crack width, and deflection
can leak calculation outcomes into a classifier. No neural network is added,
and the metrics do not authorize project use of ML. Deterministic SP63 checks
remain mandatory.

## K27 Scalable Diagnostic Dataset and Leakage-Safe Splits

K27 adds `group_key` to diagnostic rows and uses it for leakage-safe
diagnostic train/test splits. The group key is based on rectangular beam
geometry and material classes so similar variants of one section/material family
are kept on one side of the split.

The expanded diagnostic dataset can be generated at 1000 rows for ML-readiness
review. It still contains intentional fail and review cases and is not a set of
approved design solutions. Deterministic-derived ML features remain marked as
potential leakage, and no neural network is added.

## K28 Group-Diverse Diagnostic Dataset

K28 increases diagnostic group diversity by expanding geometry, cover,
material, load, span, and reinforcement-family combinations. The diagnostic
`group_key` now captures more engineering context than geometry/materials
alone, including diagnostic case type, load family, and reinforcement family.

The target review signal is `diagnostic-dataset --limit 5000 --json` with at
least 50 unique groups and `group_leakage_count = 0`. `ml-readiness
--diagnostic --json` and `ml-baseline --diagnostic-limit 1000 --json` expose
the same group-split safety indicators.

K28 does not change deterministic formulas or material values, does not add a
neural network, and does not make ML a design checker. The diagnostic dataset
remains an engineer-review artifact and is not a set of approved project
solutions.

## K29 Neural Surrogate Smoke MVP

K29 introduces the first neural-network smoke surrogate using scikit-learn
`MLPClassifier` and `MLPRegressor`. This is explicitly advisory-only and is not
a calculation module. It does not change deterministic SP63 formulas, material
catalogs, validation gates, or external validation workflow.

The neural surrogate report warns that it must not be used as a design checker,
that all ML predictions require deterministic SP63 verification, that the
diagnostic dataset is synthetic and engineer-review material, and that the
metrics are not production evidence.

Before any broader neural-network work, the project still needs engineering
review of diagnostic distributions, deterministic validation, external
validation, and ML safety policy.

## K30 ML Proposal Safety Wrapper

K30 adds a deterministic safety wrapper for advisory ML and neural-surrogate
reinforcement proposals. The wrapper rebuilds the proposed rectangular
reinforcement scheme and runs the deterministic SP63 draft checks before any
proposal can be accepted.

Acceptance requires deterministic strength status `pass`, serviceability status
`pass` or `not_checked`, and overall status `pass`. Proposals producing
`fail` or `review_or_fail` are rejected and include rejection reasons.

This step does not change formulas or material values. It reinforces the
project rule that ML is advisory-only, deterministic SP63 verification is
mandatory, and engineer review remains required even for accepted proposals.

## K31 External Validation Workflow

K31 prepares the external engineering validation workflow for comparing
`sp63_core` draft-MVP outputs with independent manual, SCAD, LIRA, or
engineer-maintained Excel results.

The step adds a public CSV template and summary report only. It does not add
closed external model files, personal documents, full normative text, or any
formula changes. External values must be filled and accepted by an engineer
before the draft-MVP can be treated as externally validated.

ML and neural surrogate modules remain advisory-only. They do not replace the
external validation workflow or deterministic SP63 checks.

## K32 External Validation Filled Sample

K32 adds a public synthetic/manual filled external validation sample aligned
with the six K20 manual verification cases. The sample checks the reporting
pipeline from program values to external/manual values, deltas,
`acceptance_status`, and summary status.

The sample is not real SCAD or LIRA evidence and does not certify the
calculation core. It uses draft acceptance tolerances for bending, shear, Mcrc,
crack width, and deflection deltas. Real external values must still be filled
and accepted by an engineer before external validation can be considered
complete.

## K33 External Validation Real-Data Gate

K33 adds strict intake checks for real engineer-filled external validation CSV
files. The step does not add real SCAD/LIRA files and does not invent external
values. It prepares validation logic for data entered by an engineer.

Strict mode checks required columns, filled external values, numeric parsing,
computed or provided deltas, tolerance limits, and consistency of
`acceptance_status`. Missing values produce review status, tolerance failures
produce fail status, and contradictory acceptance status is reported.

The engineer checklist and blank CSV template define what can be committed:
only anonymized numeric comparison rows, not closed model files, private
documents, or full normative text. ML remains advisory-only and deterministic
SP63 checks remain mandatory.

## K34 Material Catalog Engineer Verification Gate

K34 adds a verification gate for the material catalog without changing material
values or calculation formulas. The current catalog values remain draft until
an engineer fills a verification CSV or records review notes.

Verification statuses are:

- `draft`;
- `needs_review`;
- `engineer_verified`.

The gate covers concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb` and reinforcement
`Rsn`, `Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es`.

Rows can be accepted as `engineer_verified` only when `engineer_value`,
`engineer_name`, `review_date`, and `source_note` are filled and the engineer
value matches the current catalog value. Otherwise the row remains
`needs_review`.

The CSV and Markdown templates are review aids only. They must not contain full
SP 63 text, private documents, or personal data. ML remains advisory-only and
must not treat material values as final unless deterministic checks and
engineer verification both support the result.

## K35 Material Verification Report Integration

K35 adds a read-only report layer for engineer-filled material verification
CSV files. The command can emit Markdown or JSON summaries and highlights rows
that remain `needs_review`.

The report includes total rows, engineer-verified rows, rows needing review,
and missing required field counts. It does not update concrete or reinforcement
catalog values and does not change formulas.

The report is intended to support engineer review of material values before
they are treated as accepted input data. Full SP 63 text and private documents
must not be stored in the repository.

## K36 Design Calculation Report Export

K36 adds a draft rectangular design calculation report export for the existing
deterministic design workflow. The export can render Markdown, simple static
HTML, or JSON through:

```bash
python -m sp63_core design-report --markdown
python -m sp63_core design-report --html
python -m sp63_core design-report --json
```

The report includes input data, geometry, materials, selected longitudinal and
transverse reinforcement, bending and shear checks, serviceability checks,
separated statuses, warnings, and limitations.

This is a reporting layer only. It does not change formulas, material values,
reinforcement selection, ML behavior, or external validation gates. The report
is not a certified design conclusion, keeps `requires_engineer_review = true`,
and continues to require deterministic SP63 checks, material verification, and
external engineering validation.

## K37 Input-Driven Design Report

K37 extends the report export so an engineer can provide a rectangular beam
input JSON file instead of relying only on the K36 smoke example:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --html
```

The input layer validates required fields and rejects unknown fields. It then
runs the existing deterministic `design_rectangular_element()` workflow and
renders the same report structures as K36.

This is still a reporting/input layer only. It does not change deterministic
formulas, material values, reinforcement selection algorithms, ML behavior, or
external validation gates. Reports remain draft review artifacts with
`requires_engineer_review = true`.

## Next Stages

- Engineer review of material catalogs and formula cards.
- Engineer review of constructive checks.
- Dataset split and validation policy.
- Golden-case expansion.
- Baseline ML review only after deterministic checks and external validation
  gates are accepted.
