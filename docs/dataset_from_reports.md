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
