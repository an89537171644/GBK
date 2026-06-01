# GUI Technology Options

requires_engineer_review = true

## Scope

This document compares future interface options for the engineering workflow.
It is a decision-support document only. It does not add dependencies and does
not implement a GUI.

## Options

| Option | Fit | Dependency impact | K64 decision |
| --- | --- | --- | --- |
| `cli_first_no_gui` | Strong current baseline; uses tested commands and static outputs. | None. | Keep as safe baseline. |
| `static_html_report_viewer` | Good next step for report navigation and review package discovery. | None if implemented as generated static files. | Recommended direction after K64. |
| `desktop_tkinter` | Can launch local commands, but adds UI state and event-loop complexity. | Standard-library availability varies by installation. | Postpone. |
| `desktop_pyside_or_pyqt` | Strong desktop toolkit, but heavy for draft-MVP review workflow. | Heavy GUI dependency. | Not recommended now. |
| `streamlit_local_app` | Fast prototype, but dashboard framing can make outputs look authoritative. | Adds Streamlit dependency. | Forbidden in K64. |
| `gradio_local_app` | Useful for ML demos, but poor fit for deterministic engineering review. | Adds Gradio dependency. | Forbidden in K64. |
| `fastapi_web_backend` | Clean API boundary for future integration, but introduces service lifecycle concerns. | Adds server dependency. | Future-only. |
| `electron_wrapper` | Cross-platform shell, but large runtime and packaging surface. | Adds Node/Electron stack. | Not recommended now. |

## Recommended Architecture

K64 recommends:

```text
cli_first_with_static_html_reports
```

The future wrapper should launch existing commands, collect output folders,
open static HTML/Markdown/JSON reports, and show safety warnings. The wrapper
must not duplicate deterministic calculations or treat ML as a design checker.

## Safety Notes

- Deterministic SP63 output is the authority.
- ML and neural outputs remain advisory-only.
- Engineer review remains mandatory.
- Material verification and external validation remain separate gates.
- `ml_ready_for_project_use` remains false.
