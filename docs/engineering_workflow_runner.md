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

## K66 Input Form Schema

Future workflow launchers can inspect:

```bash
python -m sp63_core input-form-schema --output-dir reports/input_form_schema --json
```

The schema documents input fields and validation hints only. It does not change
the engineering workflow runner and does not approve ML for project use.

## K67 Input Preflight

Run preflight before launching the workflow when reviewing a new input JSON:

```bash
python -m sp63_core input-preflight \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/input_preflight \
  --json
```

Preflight catches missing fields, unknown fields, invalid numeric values,
unsupported material classes, and review warnings before the deterministic
workflow starts. It does not perform calculations or certify the input.

## K69 Integrated Preflight Gate

K69 connects preflight to the engineering workflow runner:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_full_smoke \
  --with-preflight \
  --with-index \
  --json
```

When enabled, the workflow writes `input_preflight_report.json` and
`input_preflight_report.md` in the workflow output folder before deterministic
report generation. `workflow_summary.json` records `preflight_status`,
`preflight_report_json_path`, `preflight_report_markdown_path`,
`preflight_errors_count`, and `preflight_warnings_count`.

If preflight returns `fail`, deterministic calculation is not run and
`deterministic_report_status`, `archive_validation_status`, and `zip_status`
are marked `skipped`. If preflight returns `review_required`, deterministic
workflow may continue, but `workflow_status` remains `review_required`.

The static index links the preflight reports when they exist. Older workflow
folders without preflight reports remain valid.

## K70 Diagnostics Catalog

Workflow-facing user messages can reference the K70 diagnostics catalog:

```bash
python -m sp63_core diagnostics-catalog --json
```

The catalog provides EN/RU titles, messages, recommended actions, and related
commands for common workflow, archive, ZIP, preflight, material, ML-readiness,
protected-file, and release-candidate diagnostics. It is guidance metadata only
and does not perform calculations.

## K71 Batch Workflow

K71 runs the existing workflow over a directory of input JSON files:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/form_templates \
  --output-dir reports/engineering_workflow_batch \
  --with-preflight \
  --with-index \
  --json
```

The batch output contains one `case_####/` folder per input file plus
`batch_workflow_summary.json`, `batch_workflow_summary.md`, `batch_index.html`,
and `README_BATCH_WORKFLOW.md`. Invalid cases are recorded as failed cases and
do not prevent remaining inputs from being processed.

## K77 Clean Batch Examples

K77 adds a clean valid batch example folder:

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/batch_valid \
  --output-dir reports/engineering_workflow_batch_valid_smoke \
  --with-preflight \
  --with-index \
  --json
```

The batch summary separates `command_exit_status` from `batch_status` and lists
`passed_cases`, `review_required_cases`, and `failed_cases`. The existing
`form_templates` folder remains a diagnostic set with intentional invalid and
review-required cases.

## K72 Evidence Templates Package

Use K72 when handing off blank evidence templates to an engineer:

```bash
python -m sp63_core evidence-templates --output-dir reports/evidence_templates --json
```

The command packages external validation and material verification CSV
templates plus a README and SHA256 manifest. The package does not contain real
external values and does not update the material catalog automatically.

## K73 Protected Files Guard

Run K73 before release-candidate review:

```bash
python -m sp63_core protected-files-check --json
```

The guard checks whether protected formula, material catalog, or
external-validation files changed in the branch diff. It is a review aid only
and does not approve a merge or project use.

## K74 User Manual

The user manual package is indexed by:

```bash
python -m sp63_core user-manual-index --json
```

The manual collects quickstart, input data, preflight, workflow, report index,
batch workflow, ML advisory limits, evidence templates, troubleshooting, and
acceptance checklist pages for engineer review.

## K75 Release Candidate Report

Use K75 for a draft release-candidate review summary:

```bash
python -m sp63_core release-candidate-report \
  --output-dir reports/release_candidate_v0_9 \
  --json
```

The report gathers golden validation, manual cases, material audit, external
validation sample, workflow self-check, input schema/preflight, static index,
protected-files guard, and user manual statuses. It is review evidence only:
it does not publish a release, certify project use, change formulas, change
material values, change reinforcement selection, implement UI, or make ML a
calculator.
