# K10 External Validation

requires_engineer_review = true

## Purpose

K10 prepares the draft MVP for external engineering validation before any
baseline ML work. It adds SCAD/LIRA comparison templates and acceptance gates
around the existing golden and dataset validation package.

## SCAD/LIRA Template

Generate a blank comparison table:

```bash
python -m sp63_core validate --external-template reports/interim/scad_lira_template.csv
```

The CSV contains program outputs from selected dataset rows:

- `program_As`;
- `program_stirrups`;
- `program_Mult`;
- `program_Qult`.

The engineer fills external values:

- `scad_As`, `scad_Mult`, `scad_Qult`;
- `lira_As`, `lira_Mult`, `lira_Qult`;
- `engineer_comment`;
- `accepted`.

## Acceptance Gates

Run:

```bash
python -m sp63_core validate \
  --golden \
  --generate-dataset-limit 100 \
  --external-template reports/interim/scad_lira_template.csv \
  --acceptance-report reports/interim/acceptance_report.json \
  --json
```

The automated gates check:

- all golden cases pass;
- dataset validation status is `pass`;
- if no external rows are filled, status is `warning`;
- when external rows are supplied, every row must have `accepted = true`;
- all filled external deltas must be less than or equal to `max_delta_percent`.

The recommended draft threshold is:

```text
max_delta_percent = 5.0
```

## Why ML Is Still Experimental

Without filled external SCAD/LIRA comparison rows and manual engineering review,
ML can only be treated as experimental. The deterministic calculation core and
dataset are still draft-MVP assets, not certified design software.
