# Workflow Run

The engineering workflow generates deterministic reports, validates the report
archive, exports a ZIP package, and can create a static index.

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow \
  --with-preflight \
  --with-index \
  --json
```

Expected files include `workflow_summary.json`, `workflow_summary.md`,
`README_WORKFLOW.md`, `deterministic_report/`, `deterministic_report.zip`, and
optional `index.html`.

If preflight fails, deterministic report generation is skipped.
