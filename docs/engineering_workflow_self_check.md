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

## Future GUI/Desktop Wrapper

K63 adds `engineering-interface-contract` for future UI planning. The contract
must be used as a safety checklist for any GUI/desktop wrapper that calls the
workflow self-check. It does not implement UI and does not certify calculations.

K64 adds `engineering-gui-planning` and recommends
`cli_first_with_static_html_reports`. A future wrapper should use self-check and
workflow outputs as static review artifacts before any GUI runtime is
considered.

K65 adds `engineering-report-index`, which can be run after a self-check output
folder is created to generate a static `index.html` over the workflow artifacts.
The index does not certify calculations and does not replace self-check,
archive validation, or engineer review.
