# Batch Engineering Workflow Runner

requires_engineer_review = true

## Purpose

K71 adds a batch runner that applies the existing `engineering-workflow` command
to every input JSON file in a directory. It is an orchestration layer only. It
does not change deterministic calculations, formulas, materials, or
reinforcement selection.

## CLI

```bash
python -m sp63_core engineering-workflow-batch \
  --input-dir docs/reports/examples/form_templates \
  --output-dir reports/engineering_workflow_batch \
  --with-preflight \
  --with-index \
  --json
```

## Output Structure

```text
reports/engineering_workflow_batch/
  case_0001/
    input_preflight_report.json
    input_preflight_report.md
    deterministic_report/
    deterministic_report.zip
    workflow_summary.json
    workflow_summary.md
    README_WORKFLOW.md
    index.html
  case_0002/
  batch_workflow_summary.json
  batch_workflow_summary.md
  batch_index.html
  README_BATCH_WORKFLOW.md
```

Each case folder is produced by the existing single-case engineering workflow.
If a case fails preflight, deterministic report generation is skipped for that
case and the batch continues to the next input file.

## Status Logic

- `pass`: all cases pass.
- `review_required`: at least one case requires review and no case fails.
- `fail`: at least one case fails.

The current form templates intentionally include invalid/review examples, so
the smoke batch is expected to complete as a process and report failed cases in
the summary.

## HTML Safety

`batch_index.html` is static navigation only. It links to case indexes or case
summaries, shows statuses, repeats required safety warnings, and performs no
calculations.

## Safety

- Batch workflow does not certify designs.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- ML remains advisory-only.
- `ml_ready_for_project_use` remains false.
