# Synthetic ML Benchmark

K55 adds a reproducible synthetic benchmark pipeline for larger report-derived
ML smoke experiments.

The benchmark is advisory-only. It is not external validation, not project
design evidence, and not certification of the calculation core. Deterministic
SP63 checks and engineer review remain mandatory.

## Pipeline

```text
guided synthetic inputs
-> design-report-batch
-> report-dataset-export
-> synthetic-dataset-balance
-> report-dataset-quality
-> report-dataset-features
-> report-ml-baseline
-> report-neural-surrogate
-> benchmark_report.json / benchmark_report.md
```

The benchmark reuses existing modules. It does not change calculation formulas,
material values, reinforcement selection, or ML safety rules.

## CLI

Smoke benchmark:

```bash
python -m sp63_core synthetic-ml-benchmark \
  --output-dir reports/synthetic_ml_benchmark_smoke \
  --target-pass 2 \
  --target-fail 2 \
  --target-review 2 \
  --seed 42 \
  --max-attempts 1000 \
  --json
```

Larger synthetic benchmark:

```bash
python -m sp63_core synthetic-ml-benchmark \
  --output-dir reports/synthetic_ml_benchmark \
  --target-pass 100 \
  --target-fail 100 \
  --target-review 100 \
  --seed 42 \
  --max-attempts 10000 \
  --json
```

Deterministic-derived feature smoke:

```bash
python -m sp63_core synthetic-ml-benchmark \
  --output-dir reports/synthetic_ml_benchmark_derived \
  --target-pass 2 \
  --target-fail 2 \
  --target-review 2 \
  --feature-mode deterministic_derived \
  --json
```

`deterministic_derived` is review-only because deterministic output values may
leak design decisions into ML features.

## Outputs

The selected output directory contains:

- `guided_inputs/`
- `batch_reports/`
- `dataset/synthetic_dataset.jsonl`
- `dataset/synthetic_dataset.csv`
- `benchmark_report.json`
- `benchmark_report.md`
- `README_BENCHMARK.md`

Large generated benchmark outputs should stay local and must not be committed.

## Statuses

- `pass` means the pipeline completed, the dataset is large enough for the
  configured benchmark gates, required classes are present, and no stage
  returned fail or review warnings.
- `review_required` means the pipeline completed but the dataset is small,
  synthetic-only, missing production evidence, or one of the gates returned
  review warnings.
- `fail` means generation, archive validation, dataset export, feature
  building, baseline ML, or neural surrogate failed.

## Limitations

- Synthetic data only.
- Not external validation.
- Material verification is separate.
- External validation is separate.
- Metrics are not production evidence.
- ML remains advisory-only.
- Neural surrogate output is not a design checker.
- Deterministic SP63 verification remains mandatory.
- Engineer review is required.
