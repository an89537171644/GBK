# Synthetic dataset balance and stratified readiness

requires_engineer_review = true

## Purpose

K53 adds a balance/readiness gate for synthetic report-derived datasets created
from K52 synthetic report inputs and K43 report dataset export.

The gate checks whether a synthetic dataset is suitable for advisory ML smoke
experiments before baseline or neural surrogate evaluation. It does not train a
model, does not approve ML output, and does not replace deterministic SP63
checks.

## Commands

JSONL dataset:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_dataset_smoke.jsonl --json
```

CSV dataset:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_dataset_smoke.csv --format csv --json
```

Optional stratified split index:

```bash
python -m sp63_core synthetic-dataset-balance \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --split-index-output reports/synthetic_split_index.json \
  --json
```

## Checked Targets

Supported targets:

- `overall_status`;
- `strength_status`;
- `serviceability_status`;
- `bending_status`;
- `shear_status`;
- `crack_width_status`;
- `deflection_status`.

For `overall_status`, the gate expects:

- `pass`;
- `fail`;
- `review_or_fail`.

Other targets are checked using their actual distribution. Constant targets
return `review_required`.

## Checks

The gate checks:

- required report-derived dataset columns;
- non-empty critical values;
- `archive_validation_status = pass`;
- advisory flags;
- target class distribution;
- minimum row count;
- minimum class count;
- class imbalance ratio;
- stratified train/validation/test split feasibility;
- leakage-like status/check columns detected by K45 logic.

Leakage-like columns may remain in the source dataset for audit and target
selection. They must not be used as input-only ML features without explicit
engineering review.

## Status Logic

- `pass` means required columns are present, archives passed validation,
  required classes are present, class counts are large enough, imbalance is
  within the configured threshold, and a stratified split is feasible.
- `review_required` means the dataset is structurally usable but needs review
  because it is synthetic-only, too small, imbalanced, missing a class, has a
  low minority class count, or lacks embedded material/external validation
  statuses.
- `fail` means the dataset is unreadable, empty, missing required/target
  columns, has empty critical values, has failed archive validation, or lacks
  mandatory advisory flags.

## Recommendations

The report can recommend:

- increasing synthetic case count;
- generating additional minority-class cases;
- adding low-load / larger-section cases for more `pass` rows;
- adding high-load / smaller-section cases for more `fail` rows;
- increasing span and service-moment combinations for serviceability review
  cases;
- using stratified sampling when imbalance is high.

## Safety Notes

- Synthetic rows are not project design data.
- Synthetic rows do not replace material verification.
- Synthetic rows do not replace external validation.
- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Every use of this gate requires engineer review.

## K54 Guided Generation

When balance recommendations indicate missing or weak classes, K54 can generate
additional synthetic inputs toward a target distribution:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --json
```

The guided generator still uses deterministic SP63 results for candidate
classification. It does not use ML to accept cases and does not turn synthetic
data into external validation.
