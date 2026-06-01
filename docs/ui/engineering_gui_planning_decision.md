# Engineering GUI Planning Decision

requires_engineer_review = true

## Purpose

K64 records the technology decision for a future minimal engineering GUI or
desktop wrapper. It is a planning artifact only. It does not implement a UI,
does not add UI dependencies, and does not change the deterministic SP63
calculation core.

## Decision

Recommended option:

```text
cli_first_with_static_html_reports
```

The current project already produces CLI-driven Markdown, HTML, JSON,
manifest, ZIP, workflow, material-verification, external-validation, and ML
readiness outputs. A future wrapper should therefore start from the CLI and
static report packages instead of adding a heavy UI runtime.

## Rationale

- Existing deterministic reports can be reviewed directly as static files.
- Existing workflow commands already expose machine-readable JSON output.
- No new UI dependency is needed for the next step.
- Deterministic SP63 results remain visually and procedurally primary.
- ML remains advisory-only and must not be presented as a design checker.
- Engineer review warnings stay easier to preserve in static report packages.

## Considered Options

- `cli_first_no_gui`
- `static_html_report_viewer`
- `desktop_tkinter`
- `desktop_pyside_or_pyqt`
- `streamlit_local_app`
- `gradio_local_app`
- `fastapi_web_backend`
- `electron_wrapper`

Heavy UI options are postponed. K64 does not add Streamlit, Gradio, Flask,
FastAPI, PyQt, PySide, Tkinter, Electron, PyTorch, TensorFlow, or Keras.

## Required Backend Commands

- `python -m sp63_core validate --golden`
- `python -m sp63_core manual-cases --json`
- `python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check --json`
- `python -m sp63_core engineering-workflow --input-json <input.json> --output-dir <output_dir> --json`
- `python -m sp63_core engineering-ml-readiness --dataset <dataset.jsonl> --external-validation-csv <external.csv> --material-verification-csv <materials.csv> --json`
- `python -m sp63_core engineering-interface-contract --output-dir <output_dir> --json`

## Safety Requirements

- ML output must never be displayed as a final design decision.
- Deterministic SP63 status must be visually primary.
- Engineer review warning must always be visible.
- `ml_ready_for_project_use` must remain false.
- Failed and `review_required` statuses must not be hidden.
- Archive validation and manifest status must be visible.
- Material verification must not update the catalog automatically.
- External validation must be shown separately from synthetic benchmark results.

## Recommended Next Step

```text
K65 - static workflow launcher and HTML report index
```

The next step should remain planning/report-package oriented: generate a static
HTML index or launcher plan around existing workflow outputs without adding a
runtime GUI dependency.

## K65 Follow-Up

K65 implements this next step as a static `index.html` generator:

```bash
python -m sp63_core engineering-report-index --workflow-dir <workflow_dir> --json
```

The index is still not a GUI framework and does not perform calculations. It is
a navigation layer over deterministic workflow outputs.

## K66 Form Schema Follow-Up

K66 adds the next planning layer: `input-form-schema`. It describes future form
fields, validation hints, and mandatory warnings while keeping the CLI/workflow
layer authoritative. It does not implement UI and keeps
`ml_ready_for_project_use = false`.

## Limitations

K64 does not implement an interface, does not certify design decisions, does
not approve ML for project use, and does not alter formulas, material values,
reinforcement selection, validation gates, report generation logic, or ML
safety rules.
