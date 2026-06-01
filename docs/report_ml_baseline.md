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

## K47 Neural Surrogate

After baseline review, the advisory neural surrogate smoke report can be run
with:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
```

The neural surrogate reuses the same K45 leakage exclusions. It is not a design
checker, metrics are not production evidence, and deterministic SP63
verification remains mandatory for any ML proposal.

## K48 Advisory Prediction

The advisory prediction command runs one input through neural prediction and
deterministic verification:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The neural prediction is compared with deterministic SP63 statuses. Mismatches
return `review_required`.

## K49 Safety Audit

K49 adds the next safety layer for the K48 command:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The audit is intended for engineer review of predicted status, deterministic
status, match result, warnings, and rejection reasons. It keeps ML
advisory-only and does not change the baseline feature or training policy.

## K50 Proposal Package

K50 adds the next packaging layer for one advisory ML proposal:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The package combines K48 prediction, K49 safety audit, deterministic SP63
statuses, class probabilities, proposal decision flags, rejection/review
reasons, and Markdown output. It does not make ML a calculator and does not
change the K46 baseline feature or training policy.

## K52 Synthetic Report Inputs

For a larger smoke dataset, generate synthetic input cases first:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
python -m sp63_core design-report-batch --input-dir reports/synthetic_inputs --output-dir reports/synthetic_batch_reports --json
python -m sp63_core report-dataset-export --path reports/synthetic_batch_reports --batch --output reports/synthetic_report_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/synthetic_report_dataset.jsonl --json
```

The baseline remains non-neural and advisory-only. Synthetic data does not
replace external validation or engineer review.

## K53 Synthetic Balance Before Baseline

Run the synthetic balance gate before interpreting baseline metrics from a
synthetic report-derived dataset:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --json
```

The gate reports whether `overall_status` has `pass`, `fail`, and
`review_or_fail`, whether minority classes are large enough, and whether a
stratified split is feasible. Baseline metrics remain advisory-only and require
engineer review.

## K54 Guided Synthetic Baseline Source

K54 can create a more balanced synthetic source before baseline evaluation:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --json
```

The baseline still uses leakage-safe feature selection and remains
advisory-only. Guided generation does not make ML a calculator.

## K55 Synthetic Benchmark

K55 runs the report-derived baseline as part of a full synthetic benchmark:

```bash
python -m sp63_core synthetic-ml-benchmark --output-dir reports/synthetic_ml_benchmark --target-pass 100 --target-fail 100 --target-review 100 --json
```

The benchmark report compares baseline metrics with neural surrogate smoke
metrics. These metrics are synthetic-only review aids and are not production
evidence.

## K56 Benchmark Model Comparison

K56 adds a comparison export for K55 benchmark reports:

```bash
python -m sp63_core benchmark-model-comparison --benchmark-report reports/synthetic_ml_benchmark/benchmark_report.json --json
```

The comparison reads the existing benchmark JSON and reports baseline vs neural
metric winners for `accuracy`, `macro_f1`, `weighted_f1`, `precision_macro`,
and `recall_macro`. It does not rerun baseline ML, does not retrain a model,
and remains advisory-only.
