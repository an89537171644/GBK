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
