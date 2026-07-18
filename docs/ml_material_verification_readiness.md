# ML Material Verification Readiness

requires_engineer_review = true

## Purpose

K59 adds a material verification readiness gate for report-derived ML datasets.
It checks whether every material class used by a dataset is covered by an
engineer-filled material verification CSV.

The gate does not approve material catalog values, does not change material
catalog values, and does not make ML a design checker.

## CLI

Dataset-only review:

```bash
python -m sp63_core ml-material-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --json
```

With the repository's synthetic fail-closed CSV fixture:

```bash
python -m sp63_core ml-material-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

CSV dataset input:

```bash
python -m sp63_core ml-material-readiness \
  --dataset reports/synthetic_dataset_smoke.csv \
  --format csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

Markdown report:

```bash
python -m sp63_core ml-material-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --markdown \
  --output reports/ml_material_readiness.md
```

## Material Keys

The gate reads these dataset columns:

- `concrete_class`;
- `longitudinal_rebar_class`;
- `stirrup_rebar_class`.

It converts them into required material keys such as:

- `concrete:B25`;
- `longitudinal_rebar:A500`;
- `stirrup_rebar:A240`.

The material verification CSV must verify all required concrete properties
`Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb` and reinforcement properties `Rsn`,
`Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es` for each required class.
Every `engineer_verified` row must also declare
`evidence_kind = independent_engineer_evidence`. The repository fixture uses
`synthetic_test_fixture`, so it intentionally remains review-required.

## Readiness Flags

- `material_verification_present` is true only when a CSV is supplied and read.
- `material_verification_complete` is true only when all required material keys
  are verified and none are missing, rejected, or still review-required.
- `material_ready_for_engineering_review` can be true for complete verified
  coverage.
- `material_ready_for_project_use` remains false.

## External Readiness Integration

`ml-external-readiness` can now receive the same CSV:

```bash
python -m sp63_core ml-external-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

`ml_ready_for_engineering_review` can be true only when the dataset is readable,
external validation has accepted cases without failures, and material
verification coverage is complete. `ml_ready_for_project_use` remains false.

## Limitations

- Material verification readiness does not certify ML output.
- Material verification does not replace external validation.
- The CSV fixture is synthetic and used for tests only; it cannot produce
  verified coverage or engineering-review readiness.
- No material catalog values are changed automatically.
- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains required.

## K60 Engineering Bundle

K60 consumes this readiness result through `engineering-ml-readiness`. Material
verification is required before the bundle can set
`ml_ready_for_engineering_review = true`:

```bash
python -m sp63_core engineering-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

The bundle does not approve catalog values and keeps
`ml_ready_for_project_use = false`.
