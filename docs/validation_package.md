# K9 Validation Package

requires_engineer_review = true

## Purpose

K9 adds a software validation package before any baseline ML work. It collects
draft golden-case checks, dataset batch checks, and a SCAD/LIRA comparison
template. This package is a validation aid, not final certification.

## Golden Validation

Run:

```bash
python -m sp63_core validate --golden
```

This executes draft golden cases for:

- rectangular bending;
- rectangular shear;
- end-to-end rectangular design.

Each result compares expected values with actual calculation-core output using
explicit tolerances. `pass` means the current code matches the stored draft
golden case. It does not mean the case is independently approved.

## Dataset Validation

Run:

```bash
python -m sp63_core validate --generate-dataset-limit 100 --json
```

The command generates draft dataset rows, creates a `group_key` split, and
checks:

- row count is nonzero;
- `unsafe_rows_count == 0`;
- `geometry_stirrup_mismatch_count == 0`;
- `duplicate_case_id_count == 0`;
- no `group_key` leakage across train/validation/test.

An existing CSV can be checked with:

```bash
python -m sp63_core validate --dataset data/generated/dataset_v001.csv
```

## JSON Report

Use `--output-report` to save the validation payload:

```bash
python -m sp63_core validate --golden --generate-dataset-limit 100 --output-report reports/interim/validation_k9.json --json
```

## SCAD/LIRA Template

`build_scad_lira_comparison_template()` returns blank comparison rows for manual
entry of SCAD/LIRA values:

- `scad_As`;
- `lira_As`;
- `scad_Mult`;
- `lira_Mult`;
- engineer comments and acceptance.

K10 also provides `build_external_comparison_rows()` and
`export_external_comparison_csv()` to create a CSV from real dataset program
outputs.

## Acceptance Gates

`evaluate_acceptance_gates()` combines:

- golden validation status;
- dataset validation status;
- optional external SCAD/LIRA rows;
- `max_delta_percent`, defaulting to `5.0`.

If external rows are not filled yet, the gate returns `warning`. If external
rows are filled, all accepted flags must be `true` and all filled deltas must be
within the allowed threshold.

## Meaning Of Pass/Fail

`pass` means the automated draft checks found no mismatch against the current
MVP rules and stored draft expectations. `fail` means the validation package
found a mismatch, unsafe row, duplicate id, stirrup geometry mismatch, or group
leakage.

## Limits

This is not final certification. Manual engineering review, external comparison
with SCAD/LIRA, and expanded golden cases are still required before ML training
or practical design use.
