# K77 Clean Batch Workflow Examples

K77 adds `docs/reports/examples/batch_valid/` as a clean smoke input folder for
`engineering-workflow-batch`.

Use it when checking that batch orchestration works without intentional invalid
input cases:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/batch_valid \
  --output-dir reports/engineering_workflow_batch_valid_smoke \
  --with-preflight \
  --with-index \
  --json
```

The older `docs/reports/examples/form_templates/` folder remains a diagnostic
set. It intentionally includes invalid and review-required inputs so the batch
runner can prove that one failed case does not stop the rest of the batch.

The batch summary now separates:

- `command_exit_status`: command/process orchestration status;
- `batch_status`: engineering aggregate status;
- `passed_cases`, `review_required_cases`, `failed_cases`;
- recommendations for fixing failed cases and reviewing non-failed cases.

This change does not alter formulas, materials, reinforcement selection, ML
policy, or external validation. Deterministic SP63 checks and engineer review
remain mandatory.
