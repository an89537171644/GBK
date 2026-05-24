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
