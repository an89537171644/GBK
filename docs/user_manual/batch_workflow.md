# Batch Workflow

Run workflow checks over a folder of input JSON files:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/form_templates \
  --output-dir reports/engineering_workflow_batch \
  --with-preflight \
  --with-index \
  --json
```

The batch runner creates one case folder per input and writes
`batch_workflow_summary.json`, `batch_workflow_summary.md`, `batch_index.html`,
and `README_BATCH_WORKFLOW.md`.

Invalid cases are reported in the batch summary and do not stop remaining
cases from running.
