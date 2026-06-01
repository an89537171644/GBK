# ML External Validation Readiness

requires_engineer_review = true

## Purpose

K58 adds an external-validation awareness layer for ML readiness. It separates
synthetic/report-derived ML datasets from datasets that also have
engineer-provided external validation and engineer-filled material verification.

This command does not train a model, does not approve ML for design use, and
does not change deterministic calculations.

## CLI

Dataset-only review:

```bash
python -m sp63_core ml-external-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --json
```

With external validation:

```bash
python -m sp63_core ml-external-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --json
```

With external validation and material verification:

```bash
python -m sp63_core ml-external-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

Markdown report:

```bash
python -m sp63_core ml-external-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --markdown \
  --output reports/ml_external_readiness.md
```

## Readiness Flags

- `ml_ready_for_research` can be true for readable deterministic
  report-derived datasets with deterministic provenance.
- `ml_ready_for_engineering_review` requires external validation support,
  complete material verification coverage, and no failed external cases.
- `ml_ready_for_project_use` is always false in K58.

K59 adds material verification coverage fields:

- `required_material_keys`;
- `verified_material_keys`;
- `missing_material_keys`;
- `rejected_material_keys`;
- `review_required_material_keys`;
- `material_coverage_ratio`;
- `material_ready_for_engineering_review`;
- `material_ready_for_project_use`.

## Limitations

- Synthetic benchmark data is not external validation.
- External validation does not make ML a design checker.
- Material verification is separate from external validation.
- Deterministic SP63 checks remain mandatory.
- ML remains advisory-only.
- Engineer review remains mandatory.
