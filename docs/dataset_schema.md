# Dataset Schema v0.1

requires_engineer_review = true

## Purpose

The dataset is a deterministic draft-MVP output of `sp63_core`. It is prepared
for future baseline ML experiments, but ML is not trained or used at this step.
Every accepted row must pass the deterministic bending, shear, layout, and
draft constructive checks.

## MVP Applicability

Only `element_type = beam` is supported in the dataset MVP. Slab constructive
logic is not fully implemented yet, so `generate_dataset_cases()` raises
`ValueError("only beam element_type is supported in dataset MVP")` when any
non-beam element type is requested.

K8 also requires the geometry stirrup diameter used for `h0` to match the
selected transverse reinforcement diameter. Dataset generation therefore limits
transverse selection to `section_stirrup_diameter` and rejects unsupported
geometry stirrup diameters.

## Fields

| field | type | units | description |
|---|---|---|---|
| `case_id` | str | - | Deterministic case id |
| `group_key` | str | - | Group identifier for leakage-safe splitting |
| `element_type` | str | - | `beam` only in MVP |
| `b` | float | mm | Section width |
| `h` | float | mm | Section height |
| `cover` | float | mm | Protective cover used for section geometry |
| `h0` | float | mm | Effective depth from selected longitudinal option section |
| `geometry_stirrup_diameter` | int | mm | Stirrup diameter used in section geometry and `h0` |
| `concrete_class` | str | - | Concrete class |
| `rebar_class` | str | - | Longitudinal reinforcement class |
| `stirrup_class` | str | - | Transverse reinforcement class |
| `load_duration` | str | - | `short` or `long` for compression reinforcement resistance |
| `M` | float | N*mm | Bending moment |
| `Q` | float | N | Shear force |
| `As_required` | float | mm2 | Selected longitudinal steel area for the checked row |
| `As_provided` | float | mm2 | Provided longitudinal steel area |
| `main_bar_count` | int | - | Number of selected tensile bars |
| `main_bar_diameter` | int | mm | Diameter of selected tensile bars |
| `main_rebar_scheme` | str | - | Example: `4D16` |
| `main_rebar_constructive_status` | str | - | Draft constructive check status |
| `main_rebar_ratio_percent` | float | % | Longitudinal reinforcement ratio |
| `main_rebar_layout_feasible` | bool | - | Single-layer layout feasibility |
| `stirrup_scheme` | str | - | Example: `D8/150, 2 legs` |
| `stirrup_diameter` | int | mm | Selected stirrup diameter |
| `stirrup_legs` | int | - | Number of stirrup legs |
| `stirrup_spacing` | int | mm | Selected stirrup spacing |
| `stirrup_Asw` | float | mm2 | Total stirrup area per spacing |
| `stirrup_steel_consumption` | float | mm2/mm | `Asw / spacing` |
| `stirrup_constructive_status` | str | - | Draft transverse constructive status |
| `stirrup_constructive_max_spacing` | float | mm | Constructive maximum spacing |
| `stirrup_sw_max_by_shear_rule` | float | mm | Draft SP 63 8.1.33 spacing limit for counting Qsw |
| `stirrup_qsw_rule_status` | str | - | `pass`, `warning`, or `not_applicable` |
| `stirrup_transverse_reinforcement_countable` | bool | - | Whether Qsw may be counted by draft rule |
| `Mult` | float | N*mm | Ultimate bending moment |
| `Qult` | float | N | Ultimate shear force |
| `bending_utilization` | float | - | `M / Mult` |
| `shear_utilization` | float | - | `Q / Qult` |
| `status` | str | - | `pass` for exported rows |
| `section_b_mm` | float | mm | Explicit K21 section width alias |
| `section_h_mm` | float | mm | Explicit K21 section height alias |
| `effective_depth_mm` | float | mm | Explicit K21 effective depth alias |
| `cover_mm` | float | mm | Explicit K21 cover alias |
| `main_bar_diameter_mm` | int | mm | Explicit K21 selected main bar diameter |
| `stirrup_diameter_mm` | int | mm | Explicit K21 selected stirrup diameter |
| `stirrup_spacing_mm` | int | mm | Explicit K21 selected stirrup spacing |
| `main_rebar_class` | str | - | Explicit K21 longitudinal reinforcement class |
| `stirrup_rebar_class` | str | - | Explicit K21 transverse reinforcement class |
| `moment_nmm` | float | N*mm | Explicit K21 bending moment |
| `shear_n` | float | N | Explicit K21 shear force |
| `moment_service_nmm` | float | N*mm | Service moment used for draft serviceability outputs |
| `span_mm` | float | mm | Span used for draft deflection output |
| `longitudinal_as_mm2` | float | mm2 | Explicit K21 selected longitudinal area |
| `transverse_asw_mm2` | float | mm2 | Explicit K21 selected transverse area |
| `bending_mult_nmm` | float | N*mm | Explicit K21 bending resistance |
| `shear_qult_n` | float | N | Explicit K21 shear resistance |
| `mcrc_nmm` | float | N*mm | Draft normal crack formation moment |
| `crack_width_mm` | float | mm | Draft normal crack width result |
| `deflection_mm` | float | mm | Draft deflection result |
| `bending_status` | str | - | Deterministic bending status |
| `shear_status` | str | - | Deterministic shear status |
| `crack_formation_status` | str | - | Draft crack formation status |
| `crack_width_status` | str | - | Draft crack width status |
| `deflection_status` | str | - | Draft deflection status |
| `strength_status` | str | - | Separated strength status from deterministic protocol |
| `serviceability_status` | str | - | Separated serviceability status from deterministic protocol |
| `overall_status` | str | - | Overall deterministic protocol status |
| `warnings_count` | int | - | Count of deterministic protocol warnings |
| `requires_engineer_review` | bool | - | Always true for draft deterministic rows |
| `unsafe_row` | bool | - | True when the row fails deterministic safety rules |
| `dataset_source` | str | - | `deterministic_sp63_core` |
| `sp63_core_version` | str | - | Calculation core version |
| `dataset_version` | str | - | Dataset schema version |

## K21 Dataset Enrichment

K21 adds explicit deterministic calculation output fields for strength and
draft serviceability checks. The generator still emits only rows that pass the
deterministic safety filters, but each row now carries the protocol statuses and
serviceability outputs used to make that decision.

The serviceability values are draft MVP outputs from the deterministic core:

- `mcrc_nmm` from normal crack formation;
- `crack_width_mm` from draft normal crack width;
- `deflection_mm` from draft short-term deflection.

The generated row includes `strength_status`, `serviceability_status`, and
`overall_status`. For exported MVP rows these are expected to be `pass`.
`unsafe_row` is expected to be `false`, and `dataset_source` is always
`deterministic_sp63_core`.

The dataset remains a deterministic draft artifact. It does not replace
engineering review, and ML remains advisory-only.

## K22 ML Readiness Gate

`python -m sp63_core ml-readiness --generate-dataset-limit 100 --json` builds a
readiness report over enriched deterministic rows. The report checks:

- required K21 input, output, status, and service metadata columns;
- status distributions for bending, shear, crack formation, crack width,
  deflection, strength, serviceability, and overall status;
- unsafe row count;
- group leakage count;
- constant target/status columns.

The current safe accepted dataset may contain only passing `overall_status`
rows. That is good for safe regression-style experiments, but it is not enough
for classification over `pass/fail/review_or_fail`. In that case the readiness
status is `review_required`, and a separate diagnostic/candidate dataset is
needed before classification ML.

K22 does not train ML and does not add a neural network. ML remains
advisory-only.

## K23 Diagnostic Dataset

`python -m sp63_core diagnostic-dataset --json` generates a separate
diagnostic/candidate dataset. This dataset is intentionally different from the
safe accepted dataset produced by `generate_dataset_cases()`.

Diagnostic rows include:

- geometry, material, load, reinforcement, strength, and serviceability fields;
- status fields for bending, shear, crack formation, crack width, deflection,
  strength, serviceability, and overall result;
- `failure_reason` and `warning_text`;
- `requires_engineer_review = true`;
- `dataset_source = diagnostic_deterministic_sp63_core`.

The default K23 diagnostic set is based on the K20 manual verification scenarios
and contains `overall_status` values `pass`, `fail`, and `review_or_fail`. It is
intended for future classification dataset preparation, not for project design.

`python -m sp63_core ml-readiness --diagnostic --json` checks the diagnostic
dataset with the K22 readiness gate. The diagnostic set is expected to require
review because it deliberately includes failing and review rows.

## K25 Expanded Diagnostic Dataset

`python -m sp63_core diagnostic-dataset --limit 100 --json` now emits an
expanded deterministic diagnostic/candidate dataset. The first six K20/K23
manual diagnostic cases are preserved, and additional candidate rows are
generated through the deterministic draft core.

Expanded diagnostic rows cover these case types:

- `pass_base`;
- `bending_fail`;
- `shear_fail`;
- `crack_review_without_width`;
- `crack_width_fail`;
- `deflection_fail`;
- `multiple_fail`.

The diagnostic status report includes distributions for `overall_status`,
`strength_status`, `serviceability_status`, and `failure_reason`. The
diagnostic dataset is for classification readiness only. It is not a set of
approved design solutions, and every row requires engineer review.

## K26 Diagnostic Baseline Feature Modes

`python -m sp63_core ml-baseline --diagnostic-limit 100 --json` evaluates the
expanded diagnostic dataset with two feature modes:

- `input_only_features`: geometry, material class codes, loads, reinforcement
  parameters, span, `As`, and `Asw`;
- `deterministic_derived_features`: input-only features plus deterministic
  outputs such as bending capacity, shear capacity, `Mcrc`, crack width, and
  deflection.

The classification target is `overall_status`. Direct status fields,
`failure_reason`, `warning_text`, and other target status columns are excluded
from the feature modes. Deterministic-derived features are flagged as
review-only because they can leak deterministic calculation outcomes into ML.

## K27 Scalable Diagnostic Dataset

`python -m sp63_core diagnostic-dataset --limit 1000 --json` emits a larger
deterministic diagnostic/candidate dataset with the same `pass`, `fail`, and
`review_or_fail` status classes. Each diagnostic row includes:

- `group_key`;
- `case_type`;
- `failure_reason`;
- strength, serviceability, and overall statuses;
- `dataset_source = diagnostic_deterministic_sp63_core`.

The diagnostic `group_key` uses rectangular beam geometry and material classes:

```text
beam_rectangular|b=<b>|h=<h>|concrete=<class>|main_rebar=<class>|stirrup_rebar=<class>
```

The group key is used for leakage-safe train/test splitting. Similar
geometry/material variants must not appear in both train and test. The
diagnostic dataset is not a design-solution dataset, and every row still
requires engineer review.

## K28 Group-Diverse Diagnostic Dataset

`python -m sp63_core diagnostic-dataset --limit 5000 --json` emits a larger
diagnostic/candidate dataset with more independent groups. K28 expands the
candidate space across section dimensions, cover, material classes, load
families, spans, and reinforcement families while preserving the K20/K23 seed
cases.

The diagnostic `group_key` now includes:

- rectangular beam element family;
- diagnostic case type;
- section width, height, and cover;
- concrete, longitudinal rebar, and stirrup rebar classes;
- load family buckets for `M`, `Q`, `Mser`, and span;
- longitudinal and transverse reinforcement family.

The diagnostic JSON report includes `unique_group_count`,
`group_key_present`, `group_leakage_count`, train/test group counts,
`overall_status` distribution, and `failure_reason` distribution. K28 expects
the 5000-row diagnostic smoke command to provide at least 50 unique groups and
zero group leakage.

The diagnostic dataset remains an ML-readiness artifact only. It is not a set
of approved project solutions, every row requires engineer review, and ML
remains advisory-only.

## K43 Report Archive Dataset

`python -m sp63_core report-dataset-export --path reports/smoke_case --output reports/smoke_dataset.jsonl --json`
exports ML-ready rows from validated report archives.

Rows use `dataset_source = "validated_report_archive"` and preserve provenance
columns for `input.json`, `report.json`, `manifest.json`, and their SHA256
checksums. The command reads generated report artifacts and does not rerun the
calculation core.

The row schema includes:

- input geometry, material classes, loads, and serviceability switches;
- selected longitudinal and transverse reinforcement;
- bending, shear, crack formation, crack width, and deflection statuses and
  main values;
- `strength_status`, `serviceability_status`, and `overall_status`;
- `requires_engineer_review = true`;
- `ml_is_advisory_only = true`;
- `deterministic_checks_required = true`.

If material verification or external validation statuses are not present in the
report archive, they are exported as `not_provided`.

This dataset is a preparation layer for future ML work only. It is not
automatically certified, does not train a model, and does not authorize using ML
as a design checker.

## K44 Report Dataset Quality Gate

`python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.jsonl --json`
checks report-derived dataset rows before ML use.

The gate verifies:

- provenance columns and SHA256 fields from report archives;
- input feature columns such as geometry, material classes, `M`, and `Q`;
- target/status candidate columns such as `strength_status`,
  `serviceability_status`, `overall_status`, and `warnings_count`;
- advisory flags `requires_engineer_review`, `ml_is_advisory_only`, and
  `deterministic_checks_required`;
- empty critical values;
- `archive_validation_status = pass`;
- `overall_status` distribution for classification readiness;
- leakage-like status/check columns that must not be used as input features
  without explicit review.

K44 does not rewrite the dataset and does not train ML. The result can be
`review_required` for small synthetic datasets or when material/external
validation statuses are still `not_provided`.

## K45 Report Dataset Feature Set

`python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json`
prepares feature, target, and split metadata for report-derived rows.

`input_only` feature mode is limited to source inputs such as geometry,
material classes, loads, service moment/span, and check switches. Status,
check-result, resistance, utilization, and direct target columns are excluded
from input features.

`deterministic_derived` adds selected deterministic outputs such as `h0`,
selected reinforcement areas, bar counts, bar diameters, and stirrup spacing.
This mode always requires review because deterministic-derived fields may leak
design decisions.

K45 reports target distribution and train/validation/test split counts. It does
not train ML and does not add neural-network code.

## K46 Report Dataset Baseline ML

`python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json`
runs a non-neural baseline classifier on the K45 feature set.

The baseline supports JSONL and CSV report-derived datasets, supported status
targets, and the `input_only` and `deterministic_derived` feature modes.
Leakage columns remain excluded from model inputs. Deterministic-derived mode
returns a warning because those fields may leak design decisions.

The command reports target distribution, split counts, metrics, confusion
matrix, feature columns, and excluded leakage columns. It returns
`review_required` for small datasets or constant targets and `fail` for missing
targets. K46 does not add neural-network code and does not make ML a design
checker.

## K29 Neural Surrogate Smoke Dataset Use

`python -m sp63_core neural-surrogate --diagnostic-limit 1000 --json` consumes
the K28 diagnostic dataset for `overall_status` classification and a safe
deterministic dataset for regression smoke targets. The command does not create
a new dataset schema, does not approve ML output, and does not save a model as
a design checker.

The diagnostic dataset remains synthetic and review-only. Neural surrogate
metrics are smoke signals, not production evidence, and deterministic SP63
checks remain mandatory for every ML prediction.

## K30 ML Proposal Verification

`python -m sp63_core ml-proposal-verify --json` verifies advisory ML proposal
examples through deterministic SP63 checks. This command does not add a new
dataset schema and does not approve ML as a project calculator.

ML proposals may include reinforcement scheme values, but they are accepted
only after deterministic verification. Unsafe or review-required proposals are
rejected, and accepted proposals still require engineer review.

## K8 Dataset Split

`split_dataset_cases()` creates reproducible train/validation/test partitions
with default ratios:

- train: 70%;
- validation: 15%;
- test: 15%.

The split uses `random.Random(seed)` and does not use ML libraries.

For honest future ML validation, `split_dataset_cases(..., group_by="group_key")`
splits by unique `group_key` values instead of individual rows. This prevents
the same geometry/material/load-duration group from appearing in both train and
validation/test.

`export_dataset_split_csv()` writes:

- `dataset_v001_train.csv`;
- `dataset_v001_validation.csv`;
- `dataset_v001_test.csv`.

## Dataset Report

`build_dataset_report()` returns:

- dataset version and total row count;
- counts by element type, concrete class, rebar class, and stirrup class;
- counts by selected longitudinal and transverse reinforcement schemes;
- min/max ranges for geometry, loads, and utilization values;
- min/max ranges for service moment, span, Mcrc, crack width, deflection, and
  warnings count;
- min/max ranges for longitudinal reinforcement ratio and stirrup steel consumption;
- counts by strength, serviceability, and overall status;
- unique group count;
- geometry stirrup mismatch count;
- duplicate case id count;
- split sizes when a split is passed;
- `unsafe_rows_count`.

`unsafe_rows_count` is the count of rows where any of these is true:

- `status != "pass"`;
- `strength_status != "pass"`;
- `serviceability_status != "pass"`;
- `overall_status != "pass"`;
- `unsafe_row is True`;
- `bending_utilization > 1.0`;
- `shear_utilization > 1.0`;
- `main_rebar_constructive_status != "pass"`;
- `stirrup_constructive_status not in ("pass", "warning")`;
- `stirrup_transverse_reinforcement_countable is not True`.

The expected value for generated MVP rows is `unsafe_rows_count = 0`.

The expected K8 value for generated MVP rows is
`geometry_stirrup_mismatch_count = 0`.

## ML Note

K12.1 adds `cover` as an explicit dataset field and removes `h0` from ML input
features. `h0` depends on the selected main bar diameter, which is an ML target,
so using it as an input feature would leak target information.

K12.2 keeps `geometry_stirrup_diameter` as an input geometry parameter and
removes `stirrup_diameter` from ML targets. In the current beam-only dataset
MVP these two values are intentionally equal, so predicting `stirrup_diameter`
would leak the target through the input geometry.

This schema supports experimental baseline ML only. It does not authorize using
an ML model as a final calculation source.
