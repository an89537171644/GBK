# Clean Batch Workflow Examples

The JSON files in this folder are valid input examples for
`engineering-workflow-batch`.

They are intended for smoke validation of batch orchestration only:

- deterministic SP63 checks remain mandatory;
- engineer review remains mandatory;
- ML remains advisory-only;
- `ml_ready_for_project_use` remains false;
- these examples do not certify any project design.

Run:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/batch_valid \
  --output-dir reports/engineering_workflow_batch_valid_smoke \
  --with-preflight \
  --with-index \
  --json
```
