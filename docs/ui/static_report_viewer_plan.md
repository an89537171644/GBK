# Static Report Viewer Plan

requires_engineer_review = true

## Purpose

This plan describes a future static report viewer or launcher layer. It is not
implemented in K64. The goal is to make generated engineering workflow outputs
easier to inspect without adding a web framework, desktop toolkit, or ML-first
interface.

## Intended Inputs

- deterministic workflow output directory;
- `workflow_summary.json`;
- `workflow_summary.md`;
- `README_WORKFLOW.md`;
- deterministic report `report.html`, `report.md`, `report.json`;
- archive `manifest.json` and ZIP validation output;
- optional engineering ML readiness bundle;
- material verification CSV/report;
- external validation CSV/report.

## Intended Viewer Sections

- project safety notice;
- deterministic calculation status;
- generated report files;
- archive and ZIP validation;
- material verification status;
- external validation status;
- optional ML readiness status;
- engineer checklist;
- warnings and error log.

## Required Backend Commands

```bash
python -m sp63_core engineering-workflow --input-json <input.json> --output-dir <output_dir> --json
python -m sp63_core engineering-workflow-self-check --output-dir reports/workflow_self_check --json
python -m sp63_core engineering-interface-contract --output-dir reports/interface_contract --json
```

## Non-Goals

- no Streamlit;
- no Gradio;
- no Flask or FastAPI;
- no PyQt or PySide;
- no Tkinter;
- no Electron;
- no calculation formula changes;
- no material catalog changes;
- no ML project approval.

## K65 Candidate

A safe K65 candidate is a generated static HTML index over an existing
engineering workflow output folder. The index should link to generated reports
and surface warnings, but all calculation and validation logic must remain in
the existing CLI/workflow layer.

## K65 Implemented Static Index

K65 implements the candidate as `engineering-report-index` and optional
`engineering-workflow --with-index`. The generated `index.html` links to
existing workflow artifacts and repeats the required warning that deterministic
SP63 verification and engineer review are mandatory.

The index remains static. It does not run calculations, start a web server, add
JavaScript calculations, or add Streamlit/Gradio/FastAPI/Flask/PyQt/PySide/
Tkinter/Electron dependencies.

## K66 Form Schema Follow-Up

K66 adds `input-form-schema` so a future static report viewer or launcher can
use a documented set of input fields and validation hints without adding a GUI
runtime or duplicating calculation logic.

## K67 Preflight Follow-Up

K67 adds `input-preflight`, which a future static launcher can run before
`engineering-workflow`:

```bash
python -m sp63_core input-preflight --input-json <input.json> --output-dir <preflight_dir> --json
```

The launcher should display the preflight status and issues, but deterministic
SP63 checks and engineer review remain mandatory.

## K68 Input Form Preview

K68 adds a static `input_form_preview.html` generator. It can help engineers
inspect the expected input fields before preparing JSON files, while keeping
all calculation and validation authority in CLI/workflow commands.
