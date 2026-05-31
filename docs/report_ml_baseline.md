# Report-derived baseline ML

requires_engineer_review = true

## Purpose

K46 runs a non-neural baseline ML evaluation on leakage-safe features prepared
from validated report-derived datasets.

The workflow is:

```text
report archive -> report-dataset-export -> report-dataset-features -> report-ml-baseline
```

K46 does not make ML a design checker. It does not add neural-network code and
does not use PyTorch, TensorFlow, or Keras. All ML output remains advisory-only
and deterministic SP63 checks remain mandatory.

## Commands

JSONL dataset:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
```

CSV dataset:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.csv --format csv --json
```

Deterministic-derived feature smoke mode:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

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

## Feature Modes

`input_only` uses source geometry, material, load, and serviceability switch
columns only. Status, direct check results, utilizations, and target columns
are excluded from features.

`deterministic_derived` can include selected deterministic outputs such as
effective depth and selected reinforcement. This mode returns a warning:

```text
deterministic-derived features may leak design decisions and must not be used for project ML decisions without review
```

## Metrics

The report includes:

- target distribution;
- train/validation/test counts;
- baseline model name;
- accuracy;
- macro F1;
- weighted F1;
- macro precision;
- macro recall;
- confusion matrix;
- excluded leakage columns.

Small datasets with fewer than 100 rows return `review_required` with a warning
that metrics are not reliable.

## Safety Notes

- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Report-derived baseline metrics require engineer review.
- K46 does not add a neural network.
- K46 does not change calculation formulas, material values, or reinforcement
  selection algorithms.
- Material verification and external validation remain separate gates.
