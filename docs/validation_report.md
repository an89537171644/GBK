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
- Draft normal crack formation check.
- Draft normal crack width check.
- Draft short-term curvature and deflection check.
- Longitudinal reinforcement selection.
- Transverse reinforcement selection.
- End-to-end rectangular design workflow.
- CLI paths for checks, selection, design, and dataset generation.

## Golden Cases

- `tests/golden_cases/bending_rectangular_case_01.md`
- `tests/golden_cases/bending_rectangular_case_02.md`
- `tests/golden_cases/shear_rectangular_case_01.md`
- `tests/golden_cases/design_rectangular_case_01.md`
- Automated K14/K15/K16 serviceability golden cases in `sp63_core.validation.golden`.

## Covered Modules

- `sp63_core.checks.bending`
- `sp63_core.checks.shear`
- `sp63_core.checks.cracking`
- `sp63_core.checks.crack_width`
- `sp63_core.checks.deflection`
- `sp63_core.rebar.longitudinal`
- `sp63_core.rebar.transverse`
- `sp63_core.rebar.constructive`
- `sp63_core.design.rectangular`
- `sp63_core.cli`

## Remaining Limits

- No long-term deflections or refined serviceability models beyond draft crack
  formation, draft crack width, and draft short-term deflection.
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
- `run_crack_formation_golden_cases()`;
- `run_crack_width_golden_cases()`;
- `run_deflection_golden_cases()`;
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

This validation covers normal crack formation only. K15 adds a separate draft
normal crack width golden case.

## K15 Normal Crack Width Validation

K15 adds a draft golden case for normal crack width in a rectangular beam:
B25 concrete, A500 reinforcement, b = 300 mm, h = 500 mm, As = 942.48 mm2,
main bar diameter 20 mm, and Mser = 30,000,000 N*mm.

The golden case checks the draft elastic cracked estimate for z, sigma_s,
epsilon_s, rho_eff, bounded crack spacing, acrc, and status.

This validation does not cover refined crack spacing, tension stiffening,
long-term effects, deflection, transformed section behavior, prestress, axial
force, slabs, T-sections, or nonlinear deformation checks.

## K16 Curvature And Deflection Validation

K16 adds a draft golden case for short-term curvature and deflection in a
rectangular beam: B25 concrete, A500 reinforcement, b = 300 mm, h = 500 mm,
As = 942.48 mm2, main bar diameter 20 mm, Mser = 30,000,000 N*mm, span =
6000 mm, deflection_limit_ratio = 250, and loading scheme
`simply_supported_uniform`.

The golden case checks I_gross, transformed cracked neutral axis depth,
I_cracked, I_eff, curvature, deflection, deflection_limit, and status.

This validation does not cover long-term deflection, creep, shrinkage, refined
tension stiffening, nonlinear deformation, slabs, columns, T-sections,
punching, torsion, anchorage, support zones, bar curtailment, or Streamlit.

## K17 Status Separation Validation

K17 updates protocol and design golden validation to include separated
`strength_status`, `serviceability_status`, and `overall_status` values. The
legacy `status` remains an alias for `overall_status`.

The design golden case keeps the same calculation values and now checks:

- `strength_status = "pass"` for bending and shear;
- `serviceability_status = "not_checked"` when serviceability checks are not
  requested;
- `overall_status = "pass"`;
- `status = "pass"`.

K17 validation changes status aggregation only. Bending, shear, crack
formation, crack width, and deflection formulas are not changed.

## K19 Material Catalog Audit

K19 adds a material audit report for the current draft concrete and
reinforcement catalog values. The report is available through:

```bash
python -m sp63_core materials-audit --json
```

The audit report is a validation smoke for catalog transparency. It confirms
that every current material property is exposed with a unit, usage note,
`draft_requires_engineer_review` status, and an explicit review flag. It does
not certify the values.

Material catalog values must still be checked manually against SP 63 tables by
an engineer before final design use. The full normative text is not stored in
the repository. ML remains advisory-only and must not treat the material catalog
as final approved design data.

## K20 Manual SP63 Verification Cases

K20 adds a manual verification package:

```bash
python -m sp63_core manual-cases --json
```

The package runs six manual control cases and compares program output against
manual expected values with documented tolerances. It also checks
`strength_status`, `serviceability_status`, and `overall_status`.

The six cases cover:

- passing beam with strength and serviceability checks;
- bending failure from insufficient longitudinal reinforcement;
- expected cracks without crack-width check;
- crack-width failure;
- deflection failure;
- shear failure.

The manual cases are a draft validation aid, not final certification. Engineer
review remains required.

## K21 Dataset Enrichment Validation

K21 expands generated dataset rows with deterministic calculation outputs and
status fields. Each generated row now records strength outputs (`Mult`, `Qult`,
utilization, bending and shear statuses), draft serviceability outputs (`Mcrc`,
crack width, deflection, and their statuses), separated protocol statuses, and
an `unsafe_row` flag.

The validation smoke keeps the existing command stable:

```bash
python -m sp63_core validate --generate-dataset-limit 20 --json
```

The enriched dataset is still produced by deterministic draft-MVP checks and is
not a final design dataset. Engineer review remains required before ML readiness
or any broader dataset generation.

## K22 ML Readiness Gate

K22 adds a dataset readiness report for later ML work:

```bash
python -m sp63_core ml-readiness --generate-dataset-limit 100 --json
```

The report checks required K21 columns, deterministic status distributions,
unsafe rows, group leakage count, constant target/status columns, and warnings.
It does not train a model.

For the current safe accepted dataset, `overall_status` can be constant `pass`.
This is intentionally reported as `review_required`: classification ML is not
ready until a separate diagnostic dataset includes fail and review cases. ML
remains advisory-only.

## K23 Diagnostic Dataset Validation

K23 adds a separate diagnostic dataset command:

```bash
python -m sp63_core diagnostic-dataset --json
```

The diagnostic dataset contains deterministic rows with `overall_status` values
`pass`, `fail`, and `review_or_fail`. The rows are based on K20 manual
verification scenarios and are computed through the existing deterministic
checks.

K23 also allows:

```bash
python -m sp63_core ml-readiness --diagnostic --json
```

This confirms that `overall_status` is no longer a constant target for the
diagnostic set. The diagnostic readiness status can still be `review_required`
because the set deliberately includes unsafe/failing rows. It is a future ML
classification aid, not a final design dataset.

## K24 Non-Neural Baseline ML Report

K24 adds a baseline ML smoke report:

```bash
python -m sp63_core ml-baseline --json
```

The report uses simple non-neural models only. It checks regression baselines
for safe deterministic dataset targets `longitudinal_as_mm2` and
`bending_utilization`, and classification baselines for `overall_status` on the
diagnostic dataset.

The report is not a design calculation and does not approve ML output. It
records that ML is advisory-only, neural networks are not used, and
deterministic SP63 checks remain mandatory. Because the diagnostic dataset is
small, classification metrics are smoke metrics and require engineer review
before any later ML stage.

## K25 Expanded Diagnostic Dataset Validation

K25 expands the diagnostic dataset command:

```bash
python -m sp63_core diagnostic-dataset --limit 100 --json
```

The command now preserves the six manual diagnostic seed cases and adds
deterministic candidate rows for pass, bending failure, shear failure,
crack-width failure, deflection failure, crack-review, and multiple-failure
scenarios. The JSON status report includes `overall_status` and
`failure_reason` distributions.

The expanded diagnostic dataset remains an engineering review artifact. It is
not a design solution set and does not authorize ML output. It exists to make
future classification readiness checks more representative before any later ML
stage.

## K26 Expanded Diagnostic Baseline ML Evaluation

K26 extends the non-neural baseline report:

```bash
python -m sp63_core ml-baseline --diagnostic-limit 100 --json
```

The JSON report now includes `expanded_diagnostic_classification` for
`overall_status` on the K25 diagnostic dataset. It reports train/test rows,
class distribution, accuracy, macro F1, per-class precision/recall, and a
confusion matrix for simple baseline classifiers.

The report includes two feature modes:

- `input_only_features`;
- `deterministic_derived_features`.

The deterministic-derived mode is explicitly flagged as review-only because it
can leak deterministic calculation results into ML classification. K26 does not
add a neural network and does not make ML a design checker. Deterministic SP63
checks remain mandatory.

## K27 Scalable Diagnostic Dataset Validation

K27 scales the diagnostic dataset command:

```bash
python -m sp63_core diagnostic-dataset --limit 1000 --json
```

Each diagnostic row now includes `group_key`. The diagnostic status report also
includes `group_key_present`, `group_leakage_count`, train/test group counts,
`overall_status` distribution, and `failure_reason` distribution.

`ml-readiness --diagnostic --json` reports group-key availability and keeps the
diagnostic set in `review_required` status when unsafe/failing rows are present.
`ml-baseline --diagnostic-limit 1000 --json` uses the diagnostic group split
when `group_key` is available and keeps the warning for deterministic-derived
feature leakage.

The diagnostic dataset is for ML-readiness and classification experiments only.
It does not authorize ML output and does not replace deterministic SP63 checks.

## K28 Group-Diverse Diagnostic Dataset Validation

K28 expands the diagnostic candidate space:

```bash
python -m sp63_core diagnostic-dataset --limit 5000 --json
```

The diagnostic JSON report now includes `unique_group_count` in addition to
`group_key_present`, `group_leakage_count`, train/test group counts,
`overall_status` distribution, and `failure_reason` distribution. The 5000-row
smoke command is expected to provide at least 50 unique diagnostic groups and
zero group leakage.

`ml-readiness --diagnostic --json` reports the same group diversity signals and
warns when diagnostic groups are too few. `ml-baseline --diagnostic-limit 1000
--json` continues to use group-aware splitting and keeps deterministic-derived
feature warnings.

The diagnostic dataset is still not a design solution set. It exists for
ML-readiness review only, and ML remains advisory-only.

## K29 Neural Surrogate Smoke MVP

K29 adds an advisory-only neural surrogate smoke command:

```bash
python -m sp63_core neural-surrogate --diagnostic-limit 1000 --json
```

The report uses scikit-learn neural-network estimators only:

- `MLPClassifier` for diagnostic `overall_status`;
- `MLPRegressor` for safe deterministic regression targets such as
  `longitudinal_as_mm2` and `bending_utilization`.

The report records classification accuracy, macro F1, confusion matrix, and
regression MAE/RMSE/R2 metrics. These metrics are smoke signals only and are not
production evidence. The neural surrogate is not a design checker, no model is
saved as a project calculator, and every ML prediction requires deterministic
SP63 verification.

## K30 ML Proposal Safety Wrapper

K30 adds deterministic verification for advisory ML proposals:

```bash
python -m sp63_core ml-proposal-verify --json
```

The smoke command verifies one passing and one failing rectangular
reinforcement proposal. The wrapper accepts a proposal only when deterministic
strength status is `pass`, serviceability status is `pass` or `not_checked`,
and overall status is `pass`.

For `rectangular_rebar_scheme` proposals, the wrapper reconstructs the proposed
reinforcement and runs deterministic bending and shear checks. When service
inputs are present, it also runs normal crack formation, crack width, and
deflection checks. Proposals with deterministic `fail` or `review_or_fail`
status are rejected.

The wrapper is a safety gate, not an ML approval mechanism. Accepted proposals
still require engineer review, and ML remains advisory-only.

## K31 External Validation Workflow

K31 adds the external validation workflow shell:

```bash
python -m sp63_core external-validation --template
python -m sp63_core external-validation --csv path/to/file.csv --json
```

The CSV template records program results and engineer-filled external values
for bending, shear, normal crack formation, crack width, deflection, and
separated strength/serviceability/overall statuses. Missing external values
produce `review_required` with a warning that the values must be filled by an
engineer.

SCAD, LIRA, Excel, or manual external values are not stored automatically in
the repository. K31 only prepares the report structure; it does not certify the
calculation core and does not change deterministic formulas.

## K32 External Validation Filled Sample Cases

K32 adds a public synthetic/manual sample:

```bash
python -m sp63_core external-validation --sample --json
```

The sample uses six K20-aligned cases and exercises:

- program values;
- external/manual values;
- delta fields;
- `acceptance_status`;
- summary status and max delta reporting.

Expected K32 sample result:

- `status = pass`;
- `accepted_cases = 6`;
- `review_cases = 0`;
- `failed_cases = 0`;
- max deltas remain within draft tolerances.

These cases are not real SCAD or LIRA files and do not replace engineer-filled
external validation. They only prove that the external-validation reporting
pipeline works end to end.

## K33 External Validation Real-Data Acceptance Gate

K33 adds strict mode for engineer-filled external validation CSV files:

```bash
python -m sp63_core external-validation --csv path/to/file.csv --strict --json
```

Strict mode reports:

- `strict_mode`;
- `missing_required_external_values_count`;
- `inconsistent_acceptance_status_count`;
- `tolerance_failed_count`;
- accepted, review, and failed case counts;
- max delta values for bending, shear, Mcrc, crack width, and deflection.

The strict gate is intended for real manual, Excel, SCAD, or LIRA comparison
values after an engineer fills an anonymized CSV. It does not add real external
files to the repository and does not invent external values.

Missing external values produce `review_required`. Tolerance failures produce
`fail`. Contradictory `acceptance_status` values are reported for engineer
review.

## K34 Material Catalog Engineer Verification Gate

K34 adds material catalog verification reporting:

```bash
python -m sp63_core materials-audit --verification-template
python -m sp63_core materials-audit --verification-csv path/to/material_verification.csv --json
python -m sp63_core material-verification --json
python -m sp63_core material-verification --template
python -m sp63_core material-verification --csv path/to/material_verification.csv --json
```

The default report is `review_required` because current catalog values are
still draft. An engineer-filled CSV can mark rows as `engineer_verified` only
when the engineer value matches the current catalog value and `engineer_name`,
`review_date`, and `source_note` are provided. Differing or incomplete values
remain `needs_review`.

K34 does not change formulas or material values. It adds an acceptance gate for
review status only, and does not store full SP 63 text.

## K35 Material Verification Report Integration

K35 adds a report command for engineer-filled material verification CSV files:

```bash
python -m sp63_core material-verification-report --csv path/to/material_verification.csv --json
python -m sp63_core material-verification-report --csv path/to/material_verification.csv --output reports/material_verification_report.md
```

The JSON summary includes `total_rows`, `engineer_verified_count`,
`needs_review_count`, and `missing_required_fields_count`. The Markdown report
lists rows that remain `needs_review`.

The report is an integration and review aid only. It does not change material
catalog values and does not certify values without engineer acceptance.

## Conclusion

The core is a draft-MVP calculation kernel. It is suitable for controlled
engineering review and small validation datasets, but it is not a final
project-design calculation tool.
