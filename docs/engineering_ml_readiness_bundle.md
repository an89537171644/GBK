# Engineering ML Readiness Bundle

requires_engineer_review = true

## Purpose

K60 adds a unified engineering ML-readiness bundle for report-derived datasets.
The bundle combines dataset quality, external validation readiness, material
verification readiness, optional synthetic benchmark/model-comparison evidence,
and optional advisory ML proposal evidence.

The bundle does not approve ML for project use. ML remains advisory-only, and
deterministic SP63 checks remain mandatory for every proposal.

## CLI

Dataset-only review:

```bash
python -m sp63_core engineering-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --json
```

With external validation and material verification:

```bash
python -m sp63_core engineering-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --output-dir reports/engineering_ml_readiness_smoke \
  --json
```

CSV dataset input:

```bash
python -m sp63_core engineering-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.csv \
  --format csv \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

Optional evidence inputs:

```bash
--benchmark-report reports/synthetic_ml_benchmark/benchmark_report.json
--benchmark-trend-report reports/benchmark_trend/benchmark_trend_report.json
--model-comparison-report reports/benchmark_comparison/model_comparison.json
--ml-proposal-package-json reports/ml_proposal_review/ml_proposal_package.json
```

Markdown and CSV views:

```bash
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --markdown
python -m sp63_core engineering-ml-readiness --dataset reports/synthetic_dataset_smoke.jsonl --csv
```

## Output Files

When `--output-dir` is supplied, the command writes:

- `engineering_ml_readiness.md`;
- `engineering_ml_readiness.json`;
- `engineering_ml_readiness_matrix.csv`;
- `README_REVIEW.md`.

## Readiness Rules

- `ml_ready_for_research` can be true when the report-derived dataset is
  readable, has advisory/deterministic flags, and the dataset quality gate does
  not fail.
- `ml_ready_for_engineering_review` can be true only when external validation
  has accepted cases without failures and material verification coverage is
  complete.
- `ml_ready_for_project_use` is always false in K60.

## Limitations

- Synthetic data is not external validation.
- Benchmark metrics are not production evidence.
- Material verification does not certify ML output.
- Advisory ML proposal packages are not design calculations.
- Engineer review remains mandatory.
