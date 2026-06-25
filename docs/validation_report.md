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

## K36 Design Calculation Report Export

K36 adds report export smoke coverage for a rectangular design calculation:

```bash
python -m sp63_core design-report --json
python -m sp63_core design-report --markdown
python -m sp63_core design-report --html
```

The report is generated from the existing deterministic rectangular design
workflow and includes bending, shear, crack formation, crack width, deflection,
and separated strength/serviceability/overall statuses for the built-in smoke
case.

The export is validation/reporting infrastructure only. It does not change
calculation formulas, material values, reinforcement selection algorithms, ML
behavior, or external validation gates. The report remains draft material and
requires engineer review.

## K37 Input-Driven Design Report Validation

K37 adds validation coverage for report generation from JSON input:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --html
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The tests verify that the example JSON loads into `RectangularDesignInput`, the
report builds, CLI output works for JSON/Markdown/HTML, output files can be
written, bundle output creates `report.md`, `report.json`, `report.html`, and
a copied `input.json`, and missing or unknown fields raise clear errors.

K37 preserves the K36 smoke mode and does not change calculation formulas,
material values, reinforcement selection algorithms, ML behavior, or external
validation gates.

## K38 Batch Design Report Validation

K38 adds validation coverage for batch report generation:

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke_json --json
```

The tests verify that batch examples create `index.md`, `index.json`, and a
case directory per input with `report.md`, `report.json`, `report.html`, and a
copied `input.json`. Invalid JSON input is represented as `input_error` in the
index without stopping valid cases.

K38 preserves the K36/K37 single-report behavior and does not change
calculation formulas, material values, reinforcement selection algorithms, ML
behavior, or external validation gates.

## K39 Report Manifest Validation

K39 adds validation coverage for report bundle manifests:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke_json --json
```

The tests verify stable SHA256 checksum calculation, single bundle
`manifest.json`, batch root and case-level manifests, and batch `index.json`
fields for manifest paths and report/input checksums.

K39 preserves report behavior and does not change calculation formulas,
material values, reinforcement selection algorithms, ML behavior, or external
validation gates.

## K40 Report Archive Validation

K40 adds validation coverage for completed report archives:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core report-archive-validate --path reports/smoke_case --json
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
```

The tests verify that valid single and batch archives pass, missing files fail,
checksum mismatches fail, missing manifests fail, and CLI JSON output works.
The batch validator also checks that `index.json` remains consistent with
case-level manifests.

K40 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K41 Report Archive ZIP Export

K41 adds validation coverage for ZIP handoff packages:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

The tests verify single and batch ZIP export, expected ZIP contents,
`zip_sha256`, CLI JSON output, and path traversal rejection for synthetic unsafe
ZIP entries.

K41 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K42 Engineering Review Package README

K42 adds validation coverage for the human-readable `README_REVIEW.md` package
guide:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core report-archive-validate --path reports/smoke_case --json
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

The tests verify that single bundles and batch roots contain
`README_REVIEW.md`, manifests include the README checksum, ZIP packages include
the README, and archive validation fails if the README is missing.

K42 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K43 Dataset Export From Report Archives

K43 adds validation coverage for `report-dataset-export`:

```bash
python -m sp63_core report-dataset-export --path reports/smoke_case --output reports/smoke_dataset.jsonl --json
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.csv --format csv --json
```

The tests verify single JSONL export, batch JSONL export, batch CSV export,
required provenance columns, engineer-review and advisory-only flags, archive
validation use, invalid archive rejection, and CLI JSON output.

K43 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K44 Report-Derived Dataset Quality Gate

K44 adds validation coverage for `report-dataset-quality`:

```bash
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.csv --format csv --json
```

The tests verify JSONL and CSV quality checks, missing required columns, empty
critical values, small dataset review status, leakage-like status/check column
warnings, missing advisory flags, non-passing archive validation status, and
CLI JSON output.

K44 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K45 Leakage-Safe Report Dataset Features

K45 adds validation coverage for `report-dataset-features`:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.csv --format csv --json
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

The tests verify JSONL and CSV feature set construction, input-only leakage
exclusion, deterministic-derived warnings, target recognition, constant target
review status, missing target failure, small dataset review status,
train/validation/test split counts, and CLI JSON output.

K45 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, ML behavior,
neural-network code, UI, or external validation gates.

## K46 Baseline ML on Report-Derived Safe Features

K46 adds validation coverage for `report-ml-baseline`:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.csv --format csv --json
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

The tests verify JSONL and CSV baseline report construction, input-only leakage
exclusion, deterministic-derived warnings, missing target failure, constant
target review status, small dataset review status, advisory-only flags, and CLI
JSON output.

K46 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, neural-network
code, UI, or external validation gates. ML remains advisory-only, and
deterministic SP63 checks remain mandatory.

## K47 Neural Surrogate v2 on Report-Derived Safe Features

K47 adds validation coverage for `report-neural-surrogate`:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.csv --format csv --json
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

The tests verify JSONL and CSV neural surrogate report construction,
input-only leakage exclusion, deterministic-derived warnings, missing target
failure, constant target review status, small dataset review status,
advisory-only flags, MLP training when possible, and CLI JSON output.

K47 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, UI, or external
validation gates. The neural surrogate remains advisory-only and is not a
design checker. Deterministic SP63 checks and engineer review remain mandatory.

## K48 Neural Advisory Prediction with Deterministic Verification

K48 adds validation coverage for `report-neural-predict`:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The tests verify JSONL and CSV advisory prediction, deterministic status
reporting, advisory-only flags, mandatory deterministic report flag,
input-only leakage exclusion, small dataset review status, missing target
failure, deterministic-derived warning, mismatch warning, and CLI JSON output.

K48 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, UI, or external
validation gates. Neural prediction remains advisory-only and is not a design
checker. Deterministic SP63 checks and engineer review remain mandatory.

## K49 Neural Advisory Safety Audit

K49 adds validation coverage for `neural-safety-audit`:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

The tests verify JSONL and CSV safety audits, deterministic status reporting,
predicted status reporting, `prediction_matches_deterministic`,
`advisory_signal_usable`, mandatory advisory-only flags, small dataset review
status, deterministic-derived warnings, mismatch rejection, Markdown output,
and `--output` file creation.

K49 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, UI, or external
validation gates. Neural prediction remains advisory-only and is not a design
checker. Deterministic SP63 checks and engineer review remain mandatory.

## K50 ML Proposal Package with Deterministic Safety Wrapper

K50 adds validation coverage for `ml-proposal-package`:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

The tests verify JSONL and CSV package construction, deterministic SP63 status
propagation, class probabilities, advisory-only flags, accepted/review/rejected
proposal decisions, mismatch rejection, deterministic fail rejection,
deterministic-derived warning, Markdown output, CLI JSON output, and `--output`
file creation.

K50 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, UI, or external
validation gates. ML proposal output remains advisory-only and is not a design
checker. Deterministic SP63 checks and engineer review remain mandatory.

## K51 ML Proposal Engineering Review Package

K51 adds validation coverage for `ml-proposal-review-package`:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review --json
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_csv --json
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_derived --json
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_nozip --no-zip --json
```

The tests verify JSONL and CSV package creation, deterministic report
MD/JSON/HTML outputs, neural safety audit MD/JSON outputs, ML proposal package
MD/JSON outputs, README_REVIEW.md, manifest checksums, ZIP contents, `--no-zip`,
deterministic-derived warnings, and CLI JSON output.

K51 preserves report generation behavior and does not change calculation
formulas, material values, reinforcement selection algorithms, UI, or external
validation gates. ZIP and manifest packaging do not certify a design. ML
remains advisory-only, deterministic SP63 checks remain mandatory, and engineer
review remains required.

## Conclusion

The core is a draft-MVP calculation kernel. It is suitable for controlled
engineering review and small validation datasets, but it is not a final
project-design calculation tool.
## K52 Synthetic Report Dataset Generation

K52 adds a reproducible synthetic input generator:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
python -m sp63_core design-report-batch --input-dir reports/synthetic_inputs --output-dir reports/synthetic_batch_reports --json
python -m sp63_core report-archive-validate --path reports/synthetic_batch_reports --batch --json
python -m sp63_core report-dataset-export --path reports/synthetic_batch_reports --batch --output reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-dataset-quality --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-dataset-features --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-neural-surrogate --dataset reports/synthetic_report_dataset.jsonl --json
```

The generator writes `README_SYNTHETIC.md` and `synthetic_manifest.json` with
per-case SHA256 checksums. Synthetic cases are not external validation and do
not certify the calculation core. ML remains advisory-only and deterministic
SP63 checks remain mandatory.

## K53 Synthetic Dataset Balance Readiness

K53 adds validation coverage for `synthetic-dataset-balance`:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_dataset_smoke.jsonl --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_dataset_smoke.csv --format csv --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_dataset_smoke.jsonl --split-index-output reports/synthetic_split_index.json --json
```

The tests verify balanced JSONL rows, CSV loading, missing class warnings and
recommendations, archive validation failure, stratified split class
preservation, CLI JSON output, and split-index output.

K53 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The balance report is a
review gate for synthetic ML experiments only.

## K54 Guided Synthetic Class Balancing

K54 adds validation coverage for `guided-synthetic-inputs`:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs_smoke --target-pass 2 --target-fail 2 --target-review 2 --seed 42 --max-attempts 500 --json
```

The tests verify guided case creation, manifest fields, deterministic
`overall_status` recording, existing input-reader compatibility, CLI JSON
output, no-serviceability review warnings, `design-report-batch` compatibility,
report-derived dataset export, and synthetic balance integration.

K54 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. Guided data is synthetic
only and requires engineer review.

## K55 Large Balanced Synthetic ML Benchmark

K55 adds validation coverage for `synthetic-ml-benchmark`:

```bash
python -m sp63_core synthetic-ml-benchmark --output-dir reports/synthetic_ml_benchmark_smoke --target-pass 2 --target-fail 2 --target-review 2 --seed 42 --max-attempts 1000 --json
python -m sp63_core synthetic-ml-benchmark --output-dir reports/synthetic_ml_benchmark_smoke_derived --target-pass 2 --target-fail 2 --target-review 2 --seed 42 --max-attempts 1000 --feature-mode deterministic_derived --json
```

The benchmark verifies the integrated synthetic pipeline from guided input
generation through batch reports, dataset export, balance/readiness gates,
feature selection, baseline ML, neural surrogate smoke metrics, and
Markdown/JSON benchmark reports.

K55 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. Benchmark data is
synthetic-only, benchmark metrics are not production evidence, and engineer
review remains required.

## K56 Benchmark Model Comparison Validation

K56 adds validation coverage for `benchmark-model-comparison`:

```bash
python -m sp63_core benchmark-model-comparison --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json --output-dir reports/benchmark_comparison_smoke --json
python -m sp63_core benchmark-model-comparison --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json --markdown
python -m sp63_core benchmark-model-comparison --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json --csv
```

The tests verify reading a K55 benchmark JSON, exporting Markdown/JSON/CSV
comparison files, per-metric winner calculation, missing metric warnings,
critical field failure handling, and CLI JSON/Markdown/CSV output.

K56 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The comparison is a
synthetic benchmark review report only; metrics are not production evidence.

## K57 Multi-Seed Benchmark Trend Validation

K57 adds validation coverage for `benchmark-trend-report`:

```bash
python -m sp63_core benchmark-trend-report --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json --output-dir reports/benchmark_trend_smoke --json
python -m sp63_core benchmark-trend-report --benchmark-dir reports --output-dir reports/benchmark_trend_discovery_smoke --json
python -m sp63_core benchmark-trend-report --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json --markdown
python -m sp63_core benchmark-trend-report --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json --csv
```

The tests verify multi-report aggregation, discovery, Markdown/JSON/CSV output,
metric mean/min/max/std calculation, winner summary counts, missing metric
warnings, and partial input-error handling.

K57 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The trend report is a
synthetic benchmark diagnostic only; trends are not production evidence.

## K58 External Validation ML Readiness Validation

K58 adds validation coverage for `ml-external-readiness`:

```bash
python -m sp63_core ml-external-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
python -m sp63_core ml-external-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --json
python -m sp63_core ml-external-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --markdown
python -m sp63_core ml-external-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --markdown --output reports/ml_external_readiness.md
```

The tests verify dataset-only review status, missing external/material
verification warnings, external validation case counts, bad CSV failure
handling, Markdown output, and CLI JSON output.

K58 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. Synthetic data is not
external validation, `ml_ready_for_project_use` remains false, and engineer
review remains mandatory.

## K59 Material Verification ML Readiness Validation

K59 adds validation coverage for `ml-material-readiness`:

```bash
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --material-verification-csv tests/fixtures/material_verification_sample.csv --json
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.csv --format csv --material-verification-csv tests/fixtures/material_verification_sample.csv --json
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --material-verification-csv tests/fixtures/material_verification_sample.csv --markdown
```

The tests verify missing-CSV review status, complete synthetic material
verification coverage, missing material keys, rejected material keys,
review-required material keys, JSONL and CSV dataset loading, CLI JSON output,
Markdown output, and integration with `ml-external-readiness`.

K59 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. Material verification
readiness does not approve catalog values, does not certify ML, and keeps
`material_ready_for_project_use` and `ml_ready_for_project_use` false.

## K60 Engineering ML Readiness Bundle Validation

K60 adds validation coverage for `engineering-ml-readiness`:

```bash
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --material-verification-csv tests/fixtures/material_verification_sample.csv --output-dir reports/engineering_ml_readiness_smoke --json
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.csv --format csv --external-validation-csv tests/fixtures/external_validation_sample.csv --material-verification-csv tests/fixtures/material_verification_sample.csv --output-dir reports/engineering_ml_readiness_csv_smoke --json
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --material-verification-csv tests/fixtures/material_verification_sample.csv --markdown
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --material-verification-csv tests/fixtures/material_verification_sample.csv --csv
```

The tests cover JSONL and CSV datasets, missing evidence review status,
complete external/material evidence, failed external validation, rejected
material verification, Markdown/JSON/CSV/README output files, and CLI JSON,
Markdown, and CSV modes.

K60 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The readiness bundle does
not approve ML for project use; `ml_ready_for_project_use` remains false.

## K61 Engineering Workflow Runner Validation

K61 adds validation coverage for `engineering-workflow`:

```bash
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_smoke --json
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_nozip_smoke --no-zip --json
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_ml_smoke --include-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --external-validation-csv tests/fixtures/external_validation_sample.csv --material-verification-csv tests/fixtures/material_verification_sample.csv --json
```

The tests verify deterministic report bundle output, archive validation, ZIP
creation, `--no-zip`, workflow summaries, `README_WORKFLOW.md`, advisory ML
readiness output, missing-dataset review warnings, and CLI JSON/Markdown modes.

K61 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The workflow is
orchestration only and does not certify project use.

## K62 Engineering Workflow Self-Check Validation

K62 adds validation coverage for `engineering-workflow-self-check`:

```bash
python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check_smoke --json
python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check_markdown_smoke --markdown
```

The tests verify deterministic workflow output creation, archive validation,
ZIP status, self-check Markdown/JSON output, optional ML readiness behavior,
missing-dataset review warnings, cleanup mode, and CLI JSON/Markdown modes.

K62 preserves calculation formulas, material values, reinforcement selection,
ML safety policy, UI, and external validation gates. The self-check is a
technical readiness check only and does not certify project use.

## K63 Engineering Interface Contract Validation

K63 adds validation coverage for the future GUI/desktop wrapper contract:

```bash
python -m sp63_core engineering-interface-contract --output-dir reports/interface_contract_smoke --json
python -m sp63_core engineering-interface-contract --output-dir reports/interface_contract_markdown_smoke --markdown
```

The tests verify required workflows, screens, inputs, outputs, warnings,
forbidden UI actions, JSON/Markdown output, CLI behavior, and safety flags.

K63 is requirements and contract work only. It does not implement UI, change
formulas, change material values, change reinforcement selection, or approve ML
for project use.

## K64 Engineering GUI Planning Decision Validation

K64 adds validation coverage for the planning-only GUI technology decision:

```bash
python -m sp63_core engineering-gui-planning --output-dir reports/gui_planning_smoke --json
python -m sp63_core engineering-gui-planning --output-dir reports/gui_planning_markdown_smoke --markdown
```

The tests verify the recommended option, considered interface options,
rejected heavy UI options, required backend commands, safety warnings,
JSON/Markdown output files, CLI behavior, and safety flags.

K64 does not implement UI, add UI dependencies, change formulas, change
material values, change reinforcement selection, or approve ML for project use.
The recommended direction is `cli_first_with_static_html_reports`;
`ml_ready_for_project_use` remains false.

## K65 Static Workflow Report Index Validation

K65 adds validation coverage for `engineering-report-index` and
`engineering-workflow --with-index`:

```bash
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_index_smoke --json
python -m sp63_core engineering-report-index --workflow-dir reports/engineering_workflow_index_smoke --json
python -m sp63_core engineering-report-index --workflow-dir reports/engineering_workflow_index_smoke --output reports/engineering_workflow_index_smoke/index_custom.html --json
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_with_index_smoke --with-index --json
```

The tests verify deterministic-only indexes, optional ML-readiness links,
required warnings, links to report HTML/Markdown/JSON, ZIP and workflow summary
files, missing-critical-file review behavior, CLI JSON output, browser-open
fallback behavior, `--with-index`, and the absence of formula-module imports.

K65 does not implement a web server or GUI framework. HTML does not perform
calculations and does not approve ML or project use.

## K66 Input Form Schema Validation

K66 adds validation coverage for the future input form schema:

```bash
python -m sp63_core input-form-schema --output-dir reports/input_form_schema_smoke --json
python -m sp63_core input-form-schema --output-dir reports/input_form_schema_markdown_smoke --markdown
```

The tests verify schema metadata, geometry/material/load/serviceability/workflow
field groups, optional ML-readiness fields, validation hints, mandatory
warnings, output JSON/Markdown files, anonymized templates, and the invariant
`ml_ready_for_project_use = false`.

K66 does not validate or modify deterministic calculation formulas. It does not
implement UI or make ML a project-use checker.

## K67 Input JSON Preflight Validation

K67 adds validation coverage for the input JSON preflight command:

```bash
python -m sp63_core input-preflight --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/input_preflight_smoke --json
python -m sp63_core input-preflight --input-json docs/reports/examples/form_templates/rectangular_serviceability_input_template.json --output-dir reports/input_preflight_markdown_smoke --markdown
```

The tests verify pass, review_required, and fail paths; missing required
fields; unknown fields; invalid JSON; non-object JSON; material class checks;
optional ML-readiness/path checks; JSON/Markdown output files; anonymized
preflight templates; and the invariant `ml_ready_for_project_use = false`.

K67 does not import or run deterministic formula modules. It does not change
formulas, material values, reinforcement selection, UI, or ML safety policy.

## K68 Static Input Form Preview Validation

K68 adds validation coverage for `input-form-preview`:

```bash
python -m sp63_core input-form-preview --output-dir reports/input_form_preview_smoke --json
```

The tests verify generated HTML/JSON/README artifacts, mandatory warning text,
geometry/material/load fields, `ml_ready_for_project_use = false`, CLI JSON and
Markdown output, `--no-output-files`, and the absence of formula-module
imports.

K68 is static preview work only. It does not implement a GUI, web server,
JavaScript calculations, project approval, formula changes, or material value
changes.

## K69 Workflow Preflight Index Integration Validation

K69 adds validation coverage for `engineering-workflow --with-preflight`:

```bash
python -m sp63_core engineering-workflow --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/engineering_workflow_full_smoke --with-preflight --with-index --json
```

The tests verify that preflight JSON and Markdown reports are created,
`workflow_summary.json` records `preflight_status` and preflight issue counts,
`index.html` links to preflight reports, invalid input stops deterministic
report generation, and workflow behavior without `--with-preflight` remains
compatible.

K69 does not change formulas, material values, reinforcement selection,
deterministic checks, UI policy, or ML safety policy.

## K70 Diagnostics Catalog Validation

K70 adds validation coverage for `diagnostics-catalog`:

```bash
python -m sp63_core diagnostics-catalog --json
python -m sp63_core diagnostics-catalog --markdown
python -m sp63_core diagnostics-catalog --output-dir reports/diagnostics_catalog_smoke --json
```

The tests verify required diagnostic codes, required categories, severity
values, EN/RU messages, recommended actions, output JSON/Markdown files, CLI
JSON/Markdown behavior, safety flags, and absence of formula-module imports.

K70 is diagnostics metadata only. It does not change formulas, material values,
reinforcement selection, deterministic checks, UI policy, or ML safety policy.

## K71 Batch Engineering Workflow Validation

K71 adds validation coverage for `engineering-workflow-batch`:

```bash
python -m sp63_core engineering-workflow-batch --input-dir docs/reports/examples/form_templates --output-dir reports/engineering_workflow_batch_smoke --with-preflight --with-index --json
```

The tests verify that the batch runner processes all JSON files in the input
directory, creates case folders, writes `batch_workflow_summary.json`,
`batch_workflow_summary.md`, `batch_index.html`, and
`README_BATCH_WORKFLOW.md`, records failed/review cases, preserves operation
when one case is invalid, provides CLI JSON output, and does not import formula
modules.

K71 is orchestration only. It does not change formulas, material values,
reinforcement selection, deterministic checks, UI policy, or ML safety policy.

## K72 Evidence Templates Package Validation

K72 adds validation coverage for `evidence-templates`:

```bash
python -m sp63_core evidence-templates --output-dir reports/evidence_templates_smoke --json
```

The tests verify that external validation and material verification templates
are copied from existing schemas, `README_EVIDENCE_TEMPLATES.md` is created,
`evidence_templates_manifest.json` records SHA256 checksums, CLI JSON works,
required safety warnings are present, and formula modules are not imported.

K72 does not create real external validation values, does not change formulas,
does not change material values, does not update the material catalog, and does
not make ML a calculator.

## K73 Protected Files Guard Validation

K73 adds validation coverage for `protected-files-check`:

```bash
python -m sp63_core protected-files-check --json
```

The tests verify the protected file list, simulated pass/fail paths, non-git
`review_required` behavior, CLI JSON output, and absence of formula-module
imports.

K73 does not change protected files. It is a review aid only and does not
approve merge, project use, formulas, materials, or ML output.

## K74 User Manual Package Validation

K74 adds validation coverage for `user-manual-index`:

```bash
python -m sp63_core user-manual-index --json
python -m sp63_core user-manual-index --markdown
```

The tests verify that all required `docs/user_manual/` files exist, output
JSON/Markdown can be written, missing-file simulation fails, CLI JSON/Markdown
works, safety flags remain present, and formula modules are not imported.

K74 is documentation only. It does not change formulas, materials,
deterministic checks, external validation logic, or ML safety policy.

## K75 Release Candidate Report Validation

K75 adds validation coverage for `release-candidate-report`:

```bash
python -m sp63_core release-candidate-report --output-dir reports/release_candidate_v0_9_smoke --json
```

The tests verify JSON/Markdown/README creation, collected status fields, known
limitations, `ml_ready_for_project_use = false`, CLI JSON/Markdown behavior,
and absence of direct formula-module imports.

K75 creates review evidence only. It does not publish a release, certify
designs, change formulas, change material values, or make ML a calculator.

## K76 CI Safety Workflow Validation

K76 adds `.github/workflows/safety.yml` and strengthens
`protected-files-check` for GitHub Actions ref handling:

```bash
python -m sp63_core protected-files-check --json
python -m sp63_core release-candidate-report --output-dir reports/release_candidate_ci_smoke --json
```

The tests verify GitHub Actions base-ref detection, JSON fields for resolved
refs, protected-file pass/fail behavior, and CLI output. The workflow uses
`fetch-depth: 0` so `origin/main` is available in CI.

K76 does not change formulas, material values, reinforcement selection,
external validation logic, or ML safety policy.

## K77 Clean Batch Examples Validation

K77 adds validation coverage for clean batch workflow examples and clearer batch
summary UX:

```bash
python -m sp63_core engineering-workflow-batch --input-dir docs/reports/examples/batch_valid --output-dir reports/engineering_workflow_batch_valid_smoke --with-preflight --with-index --json
```

The tests verify that `docs/reports/examples/batch_valid/` runs with no failed
cases, that `command_exit_status` is separate from `batch_status`, that
`passed_cases`, `review_required_cases`, `failed_cases`, and recommendations
are present in the summary, and that the older `form_templates` diagnostic set
still records intentional failed/review cases.

K77 does not change formulas, material values, reinforcement selection,
external validation logic, UI policy, or ML safety policy.

## K78 Project Template Package Validation

K78 adds validation coverage for `project-template`:

```bash
python -m sp63_core project-template --output-dir reports/project_template_smoke --json
```

The tests verify that the package creates `input/rectangular_input.json`,
external/material evidence templates, `README_PROJECT_TEMPLATE.md`,
`RUN_COMMANDS.md`, `acceptance_checklist.md`, and
`project_template_manifest.json` with SHA256 checksums. CLI JSON output,
mandatory safety flags, and absence of direct formula-module imports are also
covered.

K78 is a project handoff scaffold only. It does not run calculations, change
formulas, change material values, update the material catalog, include full
SP 63 text, include private documents, implement UI, or make ML a calculator.

## K79 Documentation Audit Validation

K79 adds validation coverage for `docs-audit`:

```bash
python -m sp63_core docs-audit --json
python -m sp63_core docs-audit --output-dir reports/docs_audit_smoke --json
```

The tests verify that required documentation files exist, local Markdown links
resolve, required CLI examples are present, JSON/Markdown report files can be
written, CLI JSON works, and direct formula-module imports are absent.

K79 is documentation infrastructure only. It does not run calculations, change
formulas, change material values, implement UI, or make ML a calculator.

## K80 Release Artifact Manifest Validation

K80 adds validation coverage for `release-manifest`:

```bash
python -m sp63_core release-manifest --output-dir reports/release_manifest_smoke --version 0.9.0-rc1 --json
```

The tests verify JSON/Markdown/VERSION output, git/version metadata, artifact
SHA256 checksums, CLI JSON/Markdown behavior, missing artifact failure, safety
flags, and absence of direct formula-module imports.

K80 is reproducibility metadata only. It does not publish a release, certify
designs, run calculations, change formulas, change material values, implement
UI, or make ML a calculator.

## K81 User Acceptance Smoke Validation

K81 adds validation coverage for `user-acceptance-smoke`:

```bash
python -m sp63_core user-acceptance-smoke --output-dir reports/user_acceptance_smoke --json
```

The tests verify aggregated smoke results for golden validation, manual cases,
external validation sample, material audit, protected-files guard, docs audit,
project template package, clean batch workflow examples, and release manifest.
They also cover CLI JSON/Markdown behavior, nested output creation, safety
flags, and absence of direct formula-module imports.

K81 is review evidence only. It does not certify designs, change formulas,
change material values, implement UI, or make ML a calculator.

## K82 v0.9 Readiness Gate Validation

K82 adds validation coverage for `v09-readiness`:

```bash
python -m sp63_core v09-readiness --output-dir reports/v09_readiness_smoke --json
python -m sp63_core v09-readiness --output-dir reports/v09_readiness_markdown_smoke --markdown
```

The tests verify that the command builds `v09_readiness_report.json`,
`v09_readiness_report.md`, nested release manifest, user acceptance smoke, and
release candidate artifacts. They also cover CLI JSON/Markdown behavior,
mandatory safety flags, `ml_ready_for_project_use = false`, and absence of
direct formula-module imports.

K82 is review evidence only. It does not publish a release, certify designs,
change formulas, change material values, implement UI, or make ML a calculator.

## K83 Material Verification Closure Validation

K83 adds validation coverage for `material-verification-closure`:

```bash
python -m sp63_core material-verification-closure --material-verification-csv tests/fixtures/material_verification_sample.csv --output-dir reports/material_verification_closure_smoke --json
```

The tests verify no-CSV review-required behavior, complete fixture readiness
for engineering review, missing material coverage, rejected material failure,
CLI JSON/Markdown behavior, `material_ready_for_project_use = false`, and
absence of direct formula-module imports.

K83 does not change formulas, material values, material catalogs,
reinforcement selection, external validation logic, or ML safety policy.

## K84 Clean Deterministic Demo Workflow Validation

K84 adds validation coverage for `clean-demo-workflow`:

```bash
python -m sp63_core clean-demo-workflow --output-dir reports/clean_demo_workflow_smoke --json
```

The tests verify that the clean demo input passes preflight and that the
deterministic workflow produces a passing report, archive validation result,
ZIP package, and static index. CLI JSON/Markdown behavior and mandatory safety
flags are covered.

K84 is workflow review evidence only. It does not certify designs, change
formulas, change material values, change reinforcement selection, implement UI,
or make ML a calculator.

## K85 Engineering Handoff Package Validation

K85 adds validation coverage for `engineering-handoff-package`:

```bash
python -m sp63_core engineering-handoff-package --output-dir reports/engineering_handoff_package_smoke --json
```

The tests verify package generation, input/demo/evidence/docs/preview files,
SHA256 manifest entries, CLI JSON output, scaffold-only README/RUN_COMMANDS
content, mandatory safety flags, and `ml_ready_for_project_use = false`.

K85 does not run calculations, change formulas, change material values,
implement UI, include private documents, or make ML a calculator.

## K86 Launcher Scripts Validation

K86 adds validation coverage for `launcher-scripts`:

```bash
python -m sp63_core launcher-scripts --output-dir reports/launcher_scripts_smoke --json
```

The tests verify `.cmd` and `.sh` script generation, manifest SHA256 checksums,
CLI JSON output, mandatory safety flags, and that scripts remain wrappers around
`python -m sp63_core` commands.

K86 does not add a GUI, start a server, change formulas, change material
values, or make ML a calculator.
