# Engineering Workflow Quickstart

## Deterministic Workflow

Run the deterministic report workflow:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_smoke \
  --json
```

Open the generated files:

- `reports/engineering_workflow_smoke/deterministic_report/report.md`;
- `reports/engineering_workflow_smoke/deterministic_report/report.json`;
- `reports/engineering_workflow_smoke/deterministic_report.zip`;
- `reports/engineering_workflow_smoke/workflow_summary.md`;
- `reports/engineering_workflow_smoke/README_WORKFLOW.md`.

## Self-Check

Before using the workflow, run:

```bash
python -m sp63_core engineering-workflow-self-check \
  --output-dir reports/workflow_self_check \
  --json
```

`self_check_status = pass` means the local workflow can generate the expected
review package artifacts. `review_required` is still normal for draft-MVP
engineering review flows and does not mean project approval.

## Engineer Review

The workflow does not certify a design. Engineer review, material verification,
external validation, and deterministic SP63 checks remain mandatory.
