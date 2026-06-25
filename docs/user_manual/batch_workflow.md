# Batch Workflow

Run workflow checks over a folder of input JSON files:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/batch_valid \
  --output-dir reports/engineering_workflow_batch_valid_smoke \
  --with-preflight \
  --with-index \
  --json
```

Use `docs/reports/examples/form_templates` when you intentionally want a
diagnostic batch with invalid and review-required examples.

The batch runner creates one case folder per input and writes
`batch_workflow_summary.json`, `batch_workflow_summary.md`, `batch_index.html`,
and `README_BATCH_WORKFLOW.md`.

Invalid cases are reported in the batch summary and do not stop remaining
cases from running.

The summary separates `command_exit_status` from `batch_status` and lists
`passed_cases`, `review_required_cases`, and `failed_cases`.
