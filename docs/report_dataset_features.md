# Report-derived ML feature set

requires_engineer_review = true

## Purpose

K45 prepares leakage-safe feature and target metadata for datasets exported from
validated report archives.

It turns:

```text
report-derived dataset -> feature set -> target set -> split metadata
```

K45 does not train ML, does not add a neural network, and does not make ML a
design checker.

## Commands

JSONL:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json
```

CSV:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.csv --format csv --json
```

Deterministic-derived feature mode:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

## Feature Modes

`input_only` includes source input columns only:

- `b`;
- `h`;
- `cover`;
- `concrete_class`;
- `longitudinal_rebar_class`;
- `stirrup_rebar_class`;
- `M`;
- `Q`;
- `Mser`;
- `span`;
- `check_cracks`;
- `check_crack_width`;
- `check_deflection`.

`deterministic_derived` additionally includes selected deterministic design
outputs such as `h0`, `longitudinal_as_mm2`, `transverse_asw_mm2`, bar counts,
bar diameters, and stirrup spacing. This mode always returns a warning because
these columns may leak design decisions.

## Leakage Exclusion

The feature set excludes target/status/check columns from inputs, including:

- `bending_status`;
- `shear_status`;
- `crack_formation_status`;
- `crack_width_status`;
- `deflection_status`;
- `strength_status`;
- `serviceability_status`;
- `overall_status`;
- `failure_reason`;
- `Mult`;
- `Qult`;
- `Mcrc`;
- `acrc`;
- `deflection`;
- utilization columns.

These columns may remain in the source dataset for audit and target use, but
must not be used as input features without explicit leakage review.

## Targets

Supported targets:

- `overall_status`;
- `strength_status`;
- `serviceability_status`;
- `bending_status`;
- `shear_status`;
- `crack_width_status`;
- `deflection_status`.

Missing targets return `status = fail`. Constant targets return
`status = review_required`.

## Split

K45 reports deterministic train/validation/test split counts. Rows are grouped
by `source_archive_path` and `case_id` where available so repeated entries for
the same archive/case are not split across partitions.

Small datasets return:

```text
status = review_required
```

with warning:

```text
dataset is too small for reliable ML training
```

## Safety Notes

- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Feature set results require engineer review.
- K45 does not train a model.
- K45 does not add PyTorch, TensorFlow, Keras, or neural network code.
- Material verification and external validation remain separate gates.

## K46 Baseline ML

After reviewing K45 feature metadata, a non-neural baseline can be run with:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.csv --format csv --json
```

`report-ml-baseline` uses the same leakage exclusions as this feature set. It
reports model metrics and a confusion matrix, but it does not approve ML for
engineering use. Small datasets and deterministic-derived feature mode require
engineer review.
