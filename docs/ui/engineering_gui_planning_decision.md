# Engineering GUI Planning Decision

requires_engineer_review = true

project_use = false

## 2026-07-19 Narrow Superseding Decision

User UAT of the standalone Windows package on 2026-07-19 found the console
workflow inconvenient for engineering use and requested an engineer-oriented
interface. Issue #134 therefore selects:

```text
desktop_tkinter
```

This selection is effective only for the Windows research trial of the
standalone rectangular-beam workflow. It supersedes K64 only where K64
postponed `desktop_tkinter` for that narrow workflow. K64 remains the historical
technology decision for the broader engineering workflow and for options not
covered by Issue #134.

Source: `UAT-2026-07-19-GUI-01`, user feedback in the project chat dated
2026-07-19. Status: `CONFIRMED` as a software-usability requirement. Architecture
impact: add a thin local window over the existing standalone controller; keep
the CLI/JSON and static-report paths. Engineering review remains required for
field meaning, applicability, status wording, and every calculation result.

The effective decision is specified in
`docs/standalone/ENGINEER_GUI_DECISION.md`. It does not authorize formula,
material, coefficient, normative-reference, or applicability changes.

## Purpose

K64 recorded the historical technology decision for a future minimal
engineering GUI or desktop wrapper. It was a planning artifact only. It did not
implement a UI, add UI dependencies, or change the deterministic SP63
calculation core.

## Decision

Historical K64 recommended option:

```text
cli_first_with_static_html_reports
```

At the time of K64, the project already produced CLI-driven Markdown, HTML, JSON,
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

Heavy UI options were postponed. K64 did not add Streamlit, Gradio, Flask,
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

## Historical Recommended Next Step

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

## K67 Preflight Follow-Up

K67 adds `input-preflight`, an executable input validation report that can be
called by a future launcher before `engineering-workflow`. It writes
`input_preflight_report.json` and `input_preflight_report.md`, but still does
not implement UI or perform design calculations.

## Limitations

K64 did not implement an interface, certify design decisions, approve ML for
project use, or alter formulas, material values, reinforcement selection,
validation gates, report generation logic, or ML safety rules. Issue #134 adds
only the narrow Tkinter standalone wrapper described above. It does not approve
ML for project use or alter formulas, material values, reinforcement selection,
validation gates, report generation logic, or ML safety rules.
