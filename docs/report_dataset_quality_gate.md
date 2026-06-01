# Report-derived dataset quality gate

requires_engineer_review = true

## Purpose

K44 adds a quality gate for datasets exported from validated report archives.
The gate is intended to run before any future ML training or evaluation that
uses `report-dataset-export` output.

K44 does not train ML, does not add a neural network, and does not make ML a
design checker. It only reports whether report-derived dataset rows are complete
enough for review.

## Command

JSONL:

```bash
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.jsonl --json
```

CSV:

```bash
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.csv --format csv --json
```

Options:

- `--task classification` checks status diversity for future classification;
- `--min-rows 100` sets the small-dataset review threshold;
- `--no-require-status-diversity` disables the pass/fail/review class warning.

## Checks

The gate checks:

- required provenance columns;
- required input feature columns;
- required target/status candidate columns;
- required advisory flags;
- empty critical values;
- `archive_validation_status = pass` for every row;
- `overall_status` distribution;
- leakage-like status/check result columns.

## Leakage Warning

Status and check-result columns such as `bending_status`, `shear_status`,
`strength_status`, and `serviceability_status` are useful labels and audit
fields, but must not be used as input features for predictive ML without an
explicit leakage review.

The quality gate reports these columns in `leakage_columns_detected`; it does
not remove or rewrite the dataset.

## Status Logic

- `pass` means required columns are present, critical values are not empty,
  archive validation passed, advisory flags are present, and no review warnings
  were triggered.
- `review_required` means the dataset is structurally usable but needs review
  because it is small, lacks classification class diversity, contains
  leakage-like columns, or lacks embedded material/external validation statuses.
- `fail` means required columns are missing, critical values are empty,
  provenance or advisory flags are incomplete, or archive validation did not
  pass.

Current synthetic report examples may return `review_required` because they are
small and do not include real material or external validation statuses.

## Safety Notes

- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Report-derived rows require engineer review.
- Material verification and external validation are separate gates.
- Full SP 63 text, personal data, grant files, and closed SCAD/LIRA files are
  not part of this workflow.

## K45 Feature Preparation

When the quality gate has been reviewed, use:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json
```

This command prepares feature and target metadata without training ML. It keeps
input-only features separate from status/check/result columns and reports which
columns were excluded as leakage risks.

## K46 Baseline ML

After feature preparation, run:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
```

The baseline command reuses the K45 leakage-safe feature selection and returns
non-neural classification metrics. `review_required` is expected for small
synthetic report datasets. The command does not change the dataset, does not
train a neural network, and does not make ML a design checker.

## K47 Neural Surrogate

The report-derived neural surrogate can be run after quality, feature, and
baseline review:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
```

It reuses K45 leakage exclusions and reports advisory-only smoke metrics.
Metrics are not production evidence, and deterministic SP63 checks remain
mandatory.

## K48 Advisory Prediction

K48 adds deterministic verification to one neural advisory prediction:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The prediction is never accepted on its own. The deterministic SP63 report for
the same input remains authoritative.

## K52 Larger Synthetic Inputs

K52 adds:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
```

The generated cases can be converted to report-derived rows through
`design-report-batch` and `report-dataset-export` before running this quality
gate. A larger synthetic set should reduce smoke-only small-dataset warnings,
but it is still synthetic data and still requires engineer review.

## K53 Synthetic Balance Readiness

K53 adds a focused balance/readiness gate for synthetic report-derived rows:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --json
```

This complements the structural quality gate by checking target distribution,
required `overall_status` classes, class imbalance, and whether a stratified
train/validation/test split can preserve all target classes. The command
reports recommendations instead of changing dataset rows.

## K54 Guided Generation

K54 can generate a synthetic input set toward the desired class distribution
before this quality gate is run:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --json
```

The generated cases are still synthetic-only and must pass through
`design-report-batch`, archive validation, dataset export, and this quality
gate before ML review.

## K55 Benchmark Quality Stage

K55 runs this quality gate inside `synthetic-ml-benchmark` after guided
generation, batch report creation, and dataset export:

```bash
python -m sp63_core synthetic-ml-benchmark --output-dir reports/synthetic_ml_benchmark --target-pass 100 --target-fail 100 --target-review 100 --json
```

The benchmark status remains `review_required` when the dataset is synthetic,
too small, or missing production evidence. It remains a review artifact, not a
design approval.
