# Engineering Workflow Self-Check

requires_engineer_review = true

## Purpose

K62 adds `engineering-workflow-self-check` as a user-facing smoke check for the
K61 engineering workflow runner. It verifies that the deterministic report
workflow can run, creates the expected review artifacts, validates the archive,
and creates the ZIP package.

The self-check does not certify the design. It only verifies that the workflow
is technically ready to run in the local environment.

## CLI

```bash
python -m sp63_core engineering-workflow-self-check \
  --output-dir reports/workflow_self_check \
  --json
```

Markdown output:

```bash
python -m sp63_core engineering-workflow-self-check \
  --output-dir reports/workflow_self_check_markdown \
  --markdown
```

With optional advisory ML readiness:

```bash
python -m sp63_core engineering-workflow-self-check \
  --output-dir reports/workflow_self_check_ml \
  --include-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

Use `--cleanup` to remove temporary workflow output folders after the self-check
report is written.

## Checked Artifacts

The deterministic self-check verifies:

- `deterministic_workflow/deterministic_report/report.md`;
- `deterministic_workflow/deterministic_report/report.json`;
- `deterministic_workflow/deterministic_report/report.html`;
- `deterministic_workflow/deterministic_report/manifest.json`;
- `deterministic_workflow/deterministic_report/README_REVIEW.md`;
- `deterministic_workflow/deterministic_report.zip`;
- `deterministic_workflow/workflow_summary.json`;
- `deterministic_workflow/workflow_summary.md`;
- `deterministic_workflow/README_WORKFLOW.md`.

## Status Rules

- `pass` means the deterministic workflow, archive validation, ZIP check, and
  required artifact checks passed.
- `review_required` means the deterministic workflow ran, but optional ML
  readiness is missing or remains review-only.
- `fail` means deterministic workflow execution, archive validation, ZIP, or
  required artifact checks failed.

## Limitations

- Self-check does not certify a calculation.
- Self-check does not approve project use.
- Material verification remains a separate engineer gate.
- External validation remains a separate engineer gate.
- ML is advisory-only.
- `ml_ready_for_project_use` must remain false.
- UI/Streamlit is not added.
