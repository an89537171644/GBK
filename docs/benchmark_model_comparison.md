# Benchmark Model Comparison

requires_engineer_review = true

## Purpose

K56 adds an advisory comparison report for K55 synthetic ML benchmark outputs.
It reads an existing `benchmark_report.json` and compares the non-neural
baseline metrics with the advisory neural surrogate metrics.

The command does not rerun the benchmark, does not train a model, and does not
change calculation formulas. It is a reporting/export layer only.

## CLI

Create Markdown, JSON, and CSV comparison files:

```bash
python -m sp63_core benchmark-model-comparison \
  --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json \
  --output-dir reports/benchmark_comparison \
  --json
```

Print Markdown only:

```bash
python -m sp63_core benchmark-model-comparison \
  --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json \
  --markdown
```

Print CSV only:

```bash
python -m sp63_core benchmark-model-comparison \
  --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json \
  --csv
```

Skip file output even when an output directory is supplied:

```bash
python -m sp63_core benchmark-model-comparison \
  --benchmark-report reports/synthetic_ml_benchmark_smoke/benchmark_report.json \
  --output-dir reports/benchmark_comparison \
  --no-output-files \
  --json
```

## Exported Files

When `--output-dir` is used, the command writes:

- `model_comparison.md`;
- `model_comparison.json`;
- `model_comparison.csv`.

Generated comparison outputs are synthetic benchmark artifacts and should not be
committed unless a future task explicitly asks for a small fixture.

## Compared Metrics

The comparison checks these metrics when present in both model reports:

- `accuracy`;
- `macro_f1`;
- `weighted_f1`;
- `precision_macro`;
- `recall_macro`.

For each metric, the report records one winner:

- `baseline`;
- `neural`;
- `tie`;
- `missing`.

Missing metrics are warnings. Missing critical benchmark fields are errors and
make the comparison status `fail`.

## Status Rules

- `pass` means the source benchmark contains the required fields and the
  comparison has no warnings.
- `review_required` means the comparison completed but warnings are present,
  for example synthetic-only data, small row counts, or missing optional
  metrics.
- `fail` means required benchmark fields are missing, the JSON cannot be read,
  or the source benchmark reports failure.

## Safety Notes

- Synthetic benchmark metrics are not production evidence.
- ML remains advisory-only.
- Neural surrogate output is not a design checker.
- Deterministic SP63 verification remains mandatory.
- Material verification and external validation remain separate gates.
- Engineer review is required before using benchmark trends for project
  decisions.
