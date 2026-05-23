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
| `sp63_core_version` | str | - | Calculation core version |
| `dataset_version` | str | - | Dataset schema version |

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
- min/max ranges for longitudinal reinforcement ratio and stirrup steel consumption;
- unique group count;
- geometry stirrup mismatch count;
- duplicate case id count;
- split sizes when a split is passed;
- `unsafe_rows_count`.

`unsafe_rows_count` is the count of rows where any of these is true:

- `status != "pass"`;
- `bending_utilization > 1.0`;
- `shear_utilization > 1.0`;
- `main_rebar_constructive_status != "pass"`;
- `stirrup_constructive_status not in ("pass", "warning")`;
- `stirrup_transverse_reinforcement_countable is not True`.

The expected value for generated MVP rows is `unsafe_rows_count = 0`.

The expected K8 value for generated MVP rows is
`geometry_stirrup_mismatch_count = 0`.

## ML Note

This schema prepares data for a future baseline ML step. It does not authorize
training, selecting, or using an ML model as a final calculation source.
