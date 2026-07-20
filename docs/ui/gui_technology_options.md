# GUI Technology Options

requires_engineer_review = true

project_use = false

## Scope

This document compares interface options for the engineering workflow. The K64
column is retained as decision history. The effective 2026-07-19 selection is a
narrow exception for the standalone rectangular-beam Windows research trial;
it does not change the broader workflow decision.

## Options

| Option | Fit | Dependency impact | Historical K64 decision | 2026-07-19 standalone trial decision |
| --- | --- | --- | --- | --- |
| `cli_first_no_gui` | Strong automation and diagnostic baseline; uses tested commands and static outputs. | None. | Keep as safe baseline. | Retain as fallback and automation path; no longer the only end-user path. |
| `static_html_report_viewer` | Good for report navigation and review package discovery. | None if implemented as generated static files. | Recommended direction after K64. | Retain for viewing generated results. |
| `desktop_tkinter` | Fits a local Windows form over the existing standalone controller. | Uses the Python installation's Tk support; availability must be checked in the Windows package. | Postponed. | **Selected only for the standalone rectangular-beam Windows research trial.** |
| `desktop_pyside_or_pyqt` | Strong desktop toolkit, but heavy for the narrow trial. | Heavy GUI dependency. | Not recommended. | Not selected. |
| `streamlit_local_app` | Fast prototype, but adds a server-like local workflow and may make diagnostic outputs look authoritative. | Adds Streamlit dependency. | Forbidden in K64. | Not selected. |
| `gradio_local_app` | Useful for ML demos, but poor fit for the deterministic standalone trial. | Adds Gradio dependency. | Forbidden in K64. | Not selected. |
| `fastapi_web_backend` | Clean API boundary for future integration, but introduces service lifecycle concerns. | Adds server dependency. | Future-only. | Outside scope. |
| `electron_wrapper` | Cross-platform shell, but large runtime and packaging surface. | Adds Node/Electron stack. | Not recommended. | Not selected. |

## Effective Narrow Architecture

Source: `UAT-2026-07-19-GUI-01`, user feedback after standalone installation
and launch on 2026-07-19. Status: `CONFIRMED` as a usability requirement.

For Issue #134, `desktop_tkinter` is a presentation adapter only:

```text
Tkinter form -> existing standalone input model/controller -> existing reports
```

The adapter must not copy calculations, introduce normative data, change
material values, or reinterpret calculation statuses. CLI/JSON remains the
diagnostic and automation fallback. Tkinter availability is a packaging and CI
acceptance condition; no automatic fallback to another GUI technology is
authorized.

This decision requires engineering review of the displayed field meanings,
units, applicability warnings, and result wording. It keeps
`requires_engineer_review = true` and `project_use = false`.

## Historical K64 Architecture

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

## K67 Input Preflight

The recommended CLI-first path now includes `input-preflight` before running
workflow commands. This keeps input validation in the backend/report layer
instead of adding UI-side calculations or a GUI dependency.

The Issue #134 Tkinter wrapper follows the same boundary: presentation-layer
validation may improve messages, but the existing model/controller validation
remains authoritative.
