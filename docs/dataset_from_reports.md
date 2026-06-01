# Dataset export from validated report archives

requires_engineer_review = true

## Purpose

K43 exports ML-ready dataset rows from already generated and validated report
archives. It reads `report.json`, `input.json`, and `manifest.json` from a
single report bundle or a batch report archive.

This export does not recalculate the deterministic SP63 core, does not train an
ML model, and does not make ML a design checker.

## Commands

Single bundle:

```bash
python -m sp63_core report-dataset-export --path reports/smoke_case --output reports/smoke_dataset.jsonl --json
```

Batch archive:

```bash
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.csv --format csv --json
```

Supported formats:

- `jsonl`;
- `json`;
- `csv`.

## Validation

Archive validation runs before export by default:

- single bundles use `report-archive-validate`;
- batch archives use `report-archive-validate --batch`.

If validation fails, export returns `status = fail` and does not write dataset
rows.

## Row Provenance

Each row includes:

- `dataset_source = "validated_report_archive"`;
- `case_id`;
- `source_archive_path`;
- `report_json_path`;
- `input_json_path`;
- `manifest_path`;
- `input_sha256`;
- `report_json_sha256`;
- `manifest_sha256`;
- `archive_validation_status`;
- `requires_engineer_review = true`;
- `ml_is_advisory_only = true`;
- `deterministic_checks_required = true`.

## Extracted Fields

Rows include input geometry, material classes, loads, selected reinforcement,
check statuses, utilizations, main deterministic results, final
`strength_status`, `serviceability_status`, `overall_status`, and
`warnings_count`.

If external validation or material verification statuses are not present in the
report, the export sets:

- `external_validation_status = "not_provided"`;
- `material_verification_status = "not_provided"`.

## Limitations

- dataset rows are prepared for future ML work only;
- the dataset is not automatically certified;
- every row requires engineer review;
- material verification and external validation must be considered separately;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory;
- no neural network is trained or added in K43.

## K44 Quality Gate

Before using report-derived rows for future ML work, run:

```bash
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-quality --dataset reports/batch_dataset.csv --format csv --json
```

The gate checks required provenance, input, status, and advisory flag columns,
empty critical values, `archive_validation_status`, status distribution, and
leakage-like status/check columns. It does not remove columns or train a model.

`review_required` is expected for small synthetic examples or rows where
material verification and external validation are still recorded as
`not_provided`.

## K45 Feature Set

After quality review, report-derived rows can be summarized into leakage-safe
feature/target metadata:

```bash
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-dataset-features --dataset reports/batch_dataset.csv --format csv --json
```

`input_only` features exclude status/check/result columns. The
`deterministic_derived` mode adds selected deterministic outputs but returns a
warning because those fields may leak design decisions.

K45 still does not train ML. The feature set requires engineer review, ML
remains advisory-only, and deterministic SP63 checks remain mandatory.

## K46 Baseline ML

After feature set review, report-derived datasets can be evaluated with a
non-neural baseline:

```bash
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-ml-baseline --dataset reports/batch_dataset.csv --format csv --json
```

The baseline uses K45 leakage exclusions, reports classification metrics and a
confusion matrix, and remains review-only. It does not approve ML output, does
not add neural-network code, and does not replace deterministic SP63 checks.

## K47 Neural Surrogate

The report-derived neural surrogate can be evaluated with:

```bash
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.jsonl --json
python -m sp63_core report-neural-surrogate --dataset reports/batch_dataset.csv --format csv --json
```

It uses the same leakage-safe report-derived feature set. It is advisory-only,
is not a design checker, and does not replace deterministic SP63 verification.
Small-dataset metrics are review-only smoke diagnostics.

## K48 Advisory Prediction

One-input advisory prediction is available with:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

The command compares the advisory prediction with a deterministic SP63 design
report generated from the same input. Mismatches require review, and the
deterministic report remains authoritative.

## K52 Synthetic Input Generation

Synthetic report input cases can be generated before running the report-derived
pipeline:

```bash
python -m sp63_core synthetic-report-inputs --output-dir reports/synthetic_inputs --case-count 300 --seed 42 --json
python -m sp63_core design-report-batch --input-dir reports/synthetic_inputs --output-dir reports/synthetic_batch_reports --json
python -m sp63_core report-dataset-export --path reports/synthetic_batch_reports --batch --output reports/synthetic_report_dataset.jsonl --json
```

The generator writes `README_SYNTHETIC.md` and `synthetic_manifest.json` next to
the input cases. Batch input discovery ignores the synthetic manifest so the
folder can be passed directly to `design-report-batch`.

Synthetic inputs are only for ML smoke experiments and pipeline checks. They do
not replace material verification, manual checks, or external validation.

## K53 Synthetic Dataset Balance

Synthetic report-derived rows can now be checked for class balance and
stratified split readiness:

```bash
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.csv --format csv --json
python -m sp63_core synthetic-dataset-balance --dataset reports/synthetic_report_dataset.jsonl --split-index-output reports/synthetic_split_index.json --json
```

The gate expects `overall_status` to include `pass`, `fail`, and
`review_or_fail`, reports imbalance and minority-class warnings, and recommends
new synthetic ranges when classes are missing. The split index is a review aid
for future ML experiments; it does not certify the dataset.

## K54 Guided Synthetic Inputs

To produce a more balanced synthetic source before report export, run:

```bash
python -m sp63_core guided-synthetic-inputs --output-dir reports/guided_synthetic_inputs --target-pass 50 --target-fail 50 --target-review 50 --seed 42 --max-attempts 3000 --json
python -m sp63_core design-report-batch --input-dir reports/guided_synthetic_inputs --output-dir reports/guided_synthetic_reports --json
python -m sp63_core report-dataset-export --path reports/guided_synthetic_reports --batch --output reports/guided_synthetic_dataset.jsonl --json
```

The guided manifest is ignored by batch input discovery. Accepted cases are
selected by deterministic `overall_status`, not ML.

## K58 External Validation Readiness

After exporting report-derived rows, run:

```bash
python -m sp63_core ml-external-readiness --dataset reports/synthetic_report_dataset.jsonl --json
```

This checks whether the dataset is synthetic/report-derived only or has
external validation and material verification support. A synthetic-only dataset
is suitable for research smoke checks but remains `review_required` for
engineering ML readiness.
