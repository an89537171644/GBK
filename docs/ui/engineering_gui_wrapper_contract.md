# Engineering GUI/Desktop Wrapper Contract

requires_engineer_review = true

## Purpose

This document defines requirements for a future engineering GUI or desktop
wrapper around the existing CLI/workflow layer. It is a contract only. It does
not implement a user interface and does not approve the software for project
use.

The future UI must call existing deterministic workflow commands instead of
duplicating or replacing calculation logic.

## Core Rules

- The UI is not the calculation core.
- The deterministic SP63 report is mandatory.
- Archive validation and ZIP integrity checks must remain visible.
- Material verification remains a separate engineer gate.
- External validation remains a separate engineer gate.
- ML and neural outputs are advisory-only.
- `ml_ready_for_project_use` must remain false.
- Engineer review remains mandatory.

## Required Workflows

- deterministic design workflow;
- workflow self-check;
- engineering ML readiness;
- optional neural advisory review;
- report archive review;
- material verification review;
- external validation review.

## Required Screens

- Start / Project Safety Notice;
- Input JSON Selection;
- Deterministic Design Report;
- Archive Validation and ZIP;
- Engineering ML Readiness;
- Material Verification;
- External Validation;
- Neural Advisory Review;
- Generated Files;
- Engineer Acceptance Checklist.

## Required Inputs

- `input_json_path`;
- `output_dir`;
- `dataset_path`;
- `external_validation_csv`;
- `material_verification_csv`;
- `include_ml_readiness`;
- `create_zip`;
- `engineer_name`;
- `review_date`;
- `source_note`.

## Required Outputs

- `deterministic_report/report.md`;
- `deterministic_report/report.json`;
- `deterministic_report/report.html`;
- `deterministic_report/manifest.json`;
- `deterministic_report.zip`;
- `workflow_summary.json`;
- `workflow_summary.md`;
- `README_WORKFLOW.md`;
- `engineering_ml_readiness.json`;
- `engineering_ml_readiness.md`;
- `engineering_ml_readiness_matrix.csv`.

## Mandatory Warnings

- This software does not certify design decisions.
- Deterministic SP63 verification is mandatory.
- Engineer review is mandatory.
- ML output is advisory-only.
- ML is not a design checker.
- `ml_ready_for_project_use` must remain false.
- Synthetic benchmarks are not external validation.
- Material verification does not certify the design automatically.
- ZIP/manifest do not certify the design.

## Forbidden UI Actions

- Hide deterministic SP63 result.
- Present ML result as final design decision.
- Allow project approval based only on ML.
- Allow `ml_ready_for_project_use = true`.
- Silence engineer-review warnings.
- Modify material catalog automatically.
- Replace deterministic report with neural prediction.
- Skip archive validation.
- Skip manifest/ZIP integrity checks.

## Recommended CLI Commands

```bash
python -m sp63_core engineering-workflow --input-json <input.json> --output-dir <output-dir> --json
python -m sp63_core engineering-workflow-self-check --output-dir <output-dir> --json
python -m sp63_core report-archive-validate --path <report-dir> --json
python -m sp63_core report-archive-zip --path <report-dir> --output <report.zip> --json
python -m sp63_core materials-audit --verification-csv <materials.csv> --json
python -m sp63_core external-validation --csv <external-validation.csv> --strict --json
```

## Limitations

K63 is requirements and interface-contract work only. It does not add Streamlit,
Qt, Flask, FastAPI, Electron, Tkinter, PyQt, or any web UI. It does not change
formulas, material values, reinforcement selection, ML policy, or external
validation gates.

## K64 Technology Decision

K64 recommends `cli_first_with_static_html_reports` as the next interface
direction. The future wrapper should organize existing static report outputs
and call the CLI/workflow layer instead of adding a heavy UI dependency or
duplicating calculations.

## K65 Static Index

K65 adds `engineering-report-index` as the first static report navigation layer.
It creates `index.html` for an existing workflow output folder and keeps the
contract rules intact: deterministic SP63 status remains primary, ML remains
advisory-only, and `ml_ready_for_project_use` remains false.

## K66 Input Schema

K66 adds a machine-readable input form schema for future wrappers. A wrapper may
use it to display fields and validation hints, but must still call the existing
CLI/workflow commands and must not perform calculations in the UI layer.

## K67 Input Preflight

K67 adds `input-preflight` as the wrapper-safe pre-run validation command:

```bash
python -m sp63_core input-preflight --input-json <input.json> --output-dir <preflight-dir> --json
```

Future wrappers should surface the preflight status and issues before launching
deterministic workflow commands. Preflight does not approve a design and does
not make ML project-ready.

## K102 Static Launcher Dashboard

K102 adds `static-launcher-dashboard`, a local static HTML launcher page that
links review commands and report artifacts. It is not a full GUI, does not run a
web server, and contains no JavaScript calculations. Deterministic SP63 checks
and engineer review remain mandatory.
