# Input JSON Preflight Validation

requires_engineer_review = true

K67 adds a preflight validator for engineering input JSON files:

```bash
python -m sp63_core input-preflight \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/input_preflight \
  --json
```

The command checks the input before a workflow run. It is a validation/reporting
step only: it does not calculate a design, approve project use, or change any
deterministic SP63 formula.

## Status Rules

- `pass`: no preflight issues were found.
- `review_required`: only review warnings were found.
- `fail`: one or more blocking input errors were found.

## Checks

- JSON must be an object.
- Required geometry, material, and load fields must be present.
- Unknown fields are rejected.
- Numeric fields must be numeric and satisfy basic engineering ranges.
- `cover < h`.
- `span > h` is screened as a review warning when span is provided.
- `M`, `Q`, and `Mser` must be nonnegative.
- `Mser > M` is flagged for engineering review.
- Material classes must exist in the current material catalog.
- `dataset_path` is required when `include_ml_readiness = true`.
- Optional external/material verification paths must exist when provided.
- `ml_ready_for_project_use` must not be user-settable and remains `false`.

## Output Files

When `--output-dir` is provided, the command writes:

- `input_preflight_report.json`;
- `input_preflight_report.md`.

Both files keep:

- `requires_engineer_review = true`;
- `ml_is_advisory_only = true`;
- `deterministic_checks_required = true`;
- `ml_ready_for_project_use = false`.

## K69 Workflow Integration

The engineering workflow can run this preflight step before deterministic
report generation:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_full_smoke \
  --with-preflight \
  --with-index \
  --json
```

If preflight fails, deterministic report generation is skipped and the workflow
returns `workflow_status = fail`. If preflight requires review, the workflow may
continue, but the summary remains `review_required`.

## Safety

Preflight is not a substitute for deterministic SP63 checks, material
verification, external validation, or engineer review. It is intended to catch
bad input early before a report, workflow, or future GUI wrapper launches the
deterministic workflow.
