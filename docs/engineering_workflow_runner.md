# Engineering Workflow Runner

requires_engineer_review = true

## Purpose

K61 adds `engineering-workflow` as an end-to-end orchestration layer for the
existing safe report workflow:

```text
input.json -> deterministic design report -> archive validation -> ZIP package
-> optional advisory ML readiness bundle
```

The workflow does not change calculation formulas, material values, or
reinforcement selection. It does not certify a design. Deterministic SP63
checks and engineer review remain mandatory.

## CLI

Deterministic report workflow:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_smoke \
  --json
```

Without ZIP packaging:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_nozip_smoke \
  --no-zip \
  --json
```

With advisory ML readiness:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_ml_smoke \
  --include-ml-readiness \
  --dataset reports/synthetic_dataset_smoke.jsonl \
  --external-validation-csv tests/fixtures/external_validation_sample.csv \
  --material-verification-csv tests/fixtures/material_verification_sample.csv \
  --json
```

The `--format csv` option can be used when the ML dataset is CSV.

## Output Structure

```text
reports/engineering_workflow/
  deterministic_report/
    input.json
    report.md
    report.json
    report.html
    manifest.json
    README_REVIEW.md
  deterministic_report.zip
  ml_readiness/
    engineering_ml_readiness.md
    engineering_ml_readiness.json
    engineering_ml_readiness_matrix.csv
    README_REVIEW.md
  workflow_summary.json
  workflow_summary.md
  README_WORKFLOW.md
```

The `ml_readiness/` folder is created only when ML readiness is requested with a
dataset path.

## Status Rules

- Archive validation or ZIP errors produce `workflow_status = fail`.
- A deterministic calculation result that needs review keeps the workflow in
  `review_required`.
- ML readiness warnings also keep the workflow in `review_required`.
- `ml_ready_for_project_use` remains false.

## Limitations

- The workflow does not certify a project design.
- Material verification is a separate engineer gate.
- External validation is a separate engineer gate.
- ML readiness is optional and advisory-only.
- Synthetic data is not external validation.
- UI/Streamlit is not added.
- Full SP 63 text is not stored in the repository.

## K62 Self-Check

Use the K62 self-check before relying on workflow outputs:

```bash
python -m sp63_core engineering-workflow-self-check \
  --output-dir reports/workflow_self_check \
  --json
```

The self-check verifies that the deterministic workflow creates the expected
report, manifest, review README, ZIP, and summary files. It does not certify the
calculation and does not replace engineer review.

## Future GUI/Desktop Wrapper

K63 defines the interface contract for a future GUI or desktop wrapper:

```bash
python -m sp63_core engineering-interface-contract --output-dir reports/interface_contract --json
```

The contract lists required screens, required inputs, required outputs,
mandatory warnings, forbidden UI actions, and recommended CLI commands. It does
not implement a UI and does not approve ML for project use.

K64 adds the planning-only technology decision:

```bash
python -m sp63_core engineering-gui-planning --output-dir reports/gui_planning --json
```

The recommended direction is `cli_first_with_static_html_reports`: keep the
CLI/workflow layer as the authority, organize existing static HTML/Markdown/JSON
outputs, and postpone heavy UI dependencies. A future interface must still show
deterministic SP63 statuses, archive validation, material verification, external
validation, engineer-review warnings, and `ml_ready_for_project_use = false`.

## Static Workflow Report Index

K65 adds a static index generator for workflow output folders:

```bash
python -m sp63_core engineering-report-index --workflow-dir reports/engineering_workflow --json
```

`engineering-workflow` can also create the index directly:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_with_index \
  --with-index \
  --json
```

The index links to existing report files and warnings only. It does not start a
server, execute calculations, approve design decisions, or change ML policy.
