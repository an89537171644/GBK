# Static Workflow Report Index

requires_engineer_review = true

## Purpose

K65 adds a static `index.html` generator for an existing engineering workflow
output folder. The index is a navigation and review aid only. It does not run a
web server, does not implement a GUI framework, and does not perform
calculations in HTML.

## CLI

Create an index in the workflow folder:

```bash
python -m sp63_core engineering-report-index \
  --workflow-dir reports/engineering_workflow_smoke \
  --json
```

Create an index at an explicit output path:

```bash
python -m sp63_core engineering-report-index \
  --workflow-dir reports/engineering_workflow_smoke \
  --output reports/engineering_workflow_smoke/index_custom.html \
  --json
```

Run the workflow and create the index in one command:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_with_index_smoke \
  --with-index \
  --json
```

## Linked Files

The index links to existing files when present:

- `deterministic_report/input.json`;
- `deterministic_report/report.md`;
- `deterministic_report/report.json`;
- `deterministic_report/report.html`;
- `deterministic_report/manifest.json`;
- `deterministic_report/README_REVIEW.md`;
- `deterministic_report.zip`;
- `workflow_summary.json`;
- `workflow_summary.md`;
- `README_WORKFLOW.md`;
- optional `ml_readiness/` review artifacts.

Missing ML readiness files produce an informational warning and do not fail the
index. Missing deterministic workflow files produce `review_required`.

## HTML Safety

The generated HTML is static and uses only plain HTML, inline CSS, and relative
links. It must not include JavaScript calculations, remote scripts, external
CDNs, forms that imply design approval, or buttons such as `Approve design`.

## Required Warning

```text
This static index does not certify the design. Deterministic SP63 verification and engineer review are mandatory. ML, if present, is advisory-only.
```

## Limitations

- static index only;
- no calculations inside HTML;
- no project approval;
- no material catalog update;
- no ML project use approval;
- deterministic SP63 report remains the primary result;
- engineer review remains mandatory;
- `ml_ready_for_project_use = false`.

## K66 Input Form Schema Link

K66 adds `input-form-schema` as metadata for a future form that could launch the
static-report workflow. The schema defines fields, validation hints, and
mandatory warnings, but it does not implement a UI and does not perform
calculations.

## K67 Input Preflight Link

K67 adds `input-preflight` as a report-only input screening step before the
workflow creates report folders and static indexes:

```bash
python -m sp63_core input-preflight --input-json <input.json> --output-dir <preflight-dir> --json
```

The static index may link to preflight artifacts in a future step, but K67 does
not alter index generation.
