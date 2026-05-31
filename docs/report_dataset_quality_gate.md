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
