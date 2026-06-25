# Engineering Workflow Preflight Integration

requires_engineer_review = true

## Purpose

K69 integrates the K67 input JSON preflight report into the engineering
workflow runner and static workflow index. The integration is orchestration
only: it does not change deterministic calculation formulas, material values,
reinforcement selection, or ML safety policy.

## CLI

Run preflight, deterministic report generation, archive validation, ZIP export,
and static index generation in one command:

```bash
python -m sp63_core engineering-workflow \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/engineering_workflow_full_smoke \
  --with-preflight \
  --with-index \
  --json
```

The output folder includes:

- `input_preflight_report.json`;
- `input_preflight_report.md`;
- `deterministic_report/`;
- `deterministic_report.zip`;
- `workflow_summary.json`;
- `workflow_summary.md`;
- `README_WORKFLOW.md`;
- `index.html` when `--with-index` is used.

## Status Handling

- `preflight_status = fail` stops deterministic report generation.
- When preflight fails, deterministic report, archive validation, and ZIP export
  are marked `skipped`.
- `workflow_status = fail` when preflight fails.
- `preflight_status = review_required` allows deterministic workflow execution,
  but the overall workflow remains `review_required`.
- Without `--with-preflight`, existing engineering workflow behavior is
  preserved and preflight fields are `null` or zero.

## Summary Fields

`workflow_summary.json` includes:

- `preflight_status`;
- `preflight_report_json_path`;
- `preflight_report_markdown_path`;
- `preflight_errors_count`;
- `preflight_warnings_count`.

The static index links preflight reports when they are present. Missing
preflight files do not make older workflow folders invalid.

## Safety

- Preflight does not perform calculations.
- The static index does not perform calculations.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- ML remains advisory-only.
- `ml_ready_for_project_use` remains false.
