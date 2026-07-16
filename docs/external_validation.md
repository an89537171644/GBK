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

Every generated row also carries mandatory provenance and hard safety fields:

- `local_axes_id`, `moment_axis`, `tension_face`, `load_duration=short`;
- `completeness_status=incomplete`;
- `evidence_status=needs_engineer_review`;
- `project_use_status=prohibited`, `project_use=false`;
- `requires_engineer_review=true`.

Legacy CSVs missing these columns, rows with `long`, and rows that attempt to
change the hard safety flags are rejected before delta evaluation.

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

After SCAD/LIRA values are filled by an engineer, run strict acceptance:

```bash
python -m sp63_core validate \
  --external-input reports/interim/scad_lira_filled.csv \
  --external-with-deltas reports/interim/scad_lira_with_deltas.csv \
  --golden \
  --generate-dataset-limit 100 \
  --acceptance-report reports/interim/acceptance_report.json \
  --json
```

The automated gates check:

- all golden cases pass;
- dataset validation status is `pass`;
- if no external rows are filled, status is `warning`;
- when external rows are supplied, every row must have `accepted = true`;
- all filled external deltas must be less than or equal to `max_delta_percent`.
- every row must have a completed external source according to
  `--required-external-source`.

The historical draft threshold is:

```text
max_delta_percent = 5.0
```

Its normative/metrological status is `OPEN_QUESTION`; it is a software gate,
not an approved engineering tolerance, until an engineer signs the policy.

`--required-external-source` accepts:

- `any`: complete SCAD or complete LIRA values;
- `scad`: complete SCAD values;
- `lira`: complete LIRA values;
- `both`: complete SCAD and LIRA values.

Use `--no-require-engineer-accepted` only for diagnostics; normal acceptance
requires `accepted = true` for every external row.

## Why ML Is Still Experimental

Without filled external SCAD/LIRA comparison rows and manual engineering review,
ML can only be treated as experimental. The deterministic calculation core and
dataset are still draft-MVP assets, not certified design software.

Even a technical external acceptance result of `pass` does not change
`completeness_status=incomplete`, `evidence_status=needs_engineer_review`, or
`project_use=false` for Step 3.
