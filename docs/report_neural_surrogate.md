# Report-derived neural surrogate

requires_engineer_review = true

## Purpose

K47 adds a neural surrogate v2 smoke report on leakage-safe report-derived
features prepared by K45 and reviewed through K46 baseline ML.

The workflow is:

```text
report archive -> report-dataset-export -> report-dataset-features -> report-neural-surrogate
```

The neural surrogate is advisory-only. It is not a design checker, does not
make project decisions, and every ML prediction requires deterministic SP63
verification and engineer review.

## Commands

JSONL dataset:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
```

CSV dataset:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.csv --format csv --json
```

Deterministic-derived feature smoke mode:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --json
```

## Feature Modes

`input_only` uses K45 leakage-safe source input columns only:

- geometry;
- material classes;
- loads;
- service moment and span;
- serviceability check switches.

Status, direct check result, utilization, and target columns are excluded from
input features.

`deterministic_derived` can include selected deterministic outputs, but it
returns this warning:

```text
deterministic-derived features may leak design decisions and must not be used for project ML decisions without review
```

## Model

K47 uses `sklearn.neural_network.MLPClassifier` only because scikit-learn is
already used by the project.

No PyTorch, TensorFlow, or Keras dependency is added.

If the target is missing, the command returns `status = fail`. If the target is
constant or the train split cannot train MLP safely, the command returns
`status = review_required`.

## Metrics

The report includes:

- target distribution;
- train/validation/test counts;
- `neural_network_used`;
- model name;
- accuracy;
- macro F1;
- weighted F1;
- macro precision;
- macro recall;
- confusion matrix;
- excluded leakage columns.

Small datasets with fewer than 100 rows return `review_required` with warning:

```text
dataset is too small for reliable neural surrogate metrics
```

Metrics are smoke diagnostics only and are not production evidence.

## Safety Notes

- Neural surrogate is advisory-only.
- Neural surrogate is not a calculation engine.
- Deterministic SP63 checks remain mandatory.
- K30 ML proposal safety wrapper remains mandatory for any ML proposal.
- Material verification and external validation remain separate gates.
- K47 does not change calculation formulas, material values, or reinforcement
  selection algorithms.
- K47 does not add PyTorch, TensorFlow, Keras, UI, Streamlit, full SP 63 text,
  personal documents, grant documents, or closed SCAD/LIRA files.

## K48 Advisory Prediction

K48 adds a single-input advisory prediction flow:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The command trains the same review-only neural surrogate style, predicts an
advisory status, then builds a deterministic SP63 design report for the input
and compares the statuses. Prediction mismatches require review.

## K49 Safety Audit

K49 wraps the K48 prediction/comparison result in an engineer-facing safety
audit:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The audit records `audit_status`, rejection reasons, warnings, and
`advisory_signal_usable`. It does not make neural output a design checker.

## K50 Proposal Package

K50 adds a proposal package layer:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The package records predicted status, class probabilities, deterministic SP63
statuses, K49 safety audit status, `proposal_status`, rejection/review reasons,
warnings, and optional Markdown output. It remains advisory-only and does not
turn the neural surrogate into a project design checker.
