# Benchmark Trend Report

requires_engineer_review = true

## Purpose

K57 adds an aggregated trend report for several K55 synthetic ML benchmark
runs. The report is intended for multi-seed review of metric stability,
class-distribution stability, and baseline-vs-neural winner trends.

The trend report reads existing `benchmark_report.json` files. It does not run
the K55 benchmark, does not train models, and does not change the deterministic
calculation core.

## CLI

Use repeated benchmark report paths:

```bash
python -m sp63_core benchmark-trend-report \
  --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json \
  --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json \
  --output-dir reports/benchmark_trend \
  --json
```

Use recursive discovery:

```bash
python -m sp63_core benchmark-trend-report \
  --benchmark-dir reports/benchmark_runs \
  --output-dir reports/benchmark_trend \
  --json
```

Print Markdown:

```bash
python -m sp63_core benchmark-trend-report \
  --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json \
  --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json \
  --markdown
```

Print CSV trend rows:

```bash
python -m sp63_core benchmark-trend-report \
  --benchmark-report reports/synthetic_ml_benchmark_seed_1/benchmark_report.json \
  --benchmark-report reports/synthetic_ml_benchmark_seed_2/benchmark_report.json \
  --csv
```

## Exported Files

When `--output-dir` is provided, K57 writes:

- `benchmark_trend_report.md`;
- `benchmark_trend_report.json`;
- `benchmark_trend_metrics.csv`;
- `benchmark_trend_winners.csv`.

Generated trend outputs are synthetic benchmark artifacts and should not be
committed unless a future task explicitly asks for a small fixture.

## Aggregated Fields

K57 aggregates:

- benchmark report paths;
- dataset row counts;
- final `pass`, `fail`, and `review_or_fail` distributions;
- baseline metric summaries;
- neural metric summaries;
- per-metric winner counts;
- recommendations;
- warnings and input errors.

The metric summary covers:

- `accuracy`;
- `macro_f1`;
- `weighted_f1`;
- `precision_macro`;
- `recall_macro`.

For each metric and model, the report records `count`, `mean`, `min`, `max`,
`std`, and `missing_count`.

## Status Rules

- `pass` is possible only when enough valid benchmark reports and rows are
  present, required classes are present, metrics are present, and there are no
  warnings or critical errors.
- `review_required` means at least one valid report was read but trend evidence
  is limited, synthetic-only, small, warning-bearing, or incomplete.
- `fail` means no valid benchmark report is available or metric summaries
  cannot be formed.

Smoke runs with two 6-row benchmark reports are expected to return
`review_required`.

## Safety Notes

- Synthetic benchmark trends are not external validation.
- Synthetic metrics are not production evidence.
- ML remains advisory-only.
- Neural surrogate output is not a design checker.
- Deterministic SP63 verification remains mandatory.
- Material verification and external validation remain separate gates.
- Engineer review is required before using trend reports for engineering
  decisions.
- For engineering conclusions, use external validation cases and
  engineer-verified materials.

## K58 External Validation Awareness

K58 adds `ml-external-readiness` after the synthetic trend layer. The command
does not reinterpret K57 metrics; it checks whether a report-derived ML dataset
has external validation and material verification support.

Synthetic benchmark trends remain synthetic-only evidence. External validation
CSV files and material verification CSV files must be supplied separately
before any engineering ML review.

## K59 Material Verification Readiness

K59 adds a separate material verification readiness command for report-derived
datasets:

```bash
python -m sp63_core ml-material-readiness --dataset reports/synthetic_dataset_smoke.jsonl --json
```

When an engineer-filled material verification CSV is supplied, the report lists
required, verified, missing, rejected, and review-required material keys. Trend
metrics still remain synthetic-only and cannot be interpreted as engineering
evidence without external validation and material verification review.

## K60 Engineering Bundle

K60 can reference `benchmark_trend_report.json` as optional trend evidence:

```bash
python -m sp63_core engineering-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --benchmark-trend-report reports/benchmark_trend/benchmark_trend_report.json \
  --json
```

Trend evidence remains synthetic-only and review-only. It is not external
validation and does not change `ml_ready_for_project_use = false`.
