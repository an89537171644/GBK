# Portable Windows Package Skeleton

K93 adds a portable Windows-oriented package skeleton without building an exe or
adding UI dependencies.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Command

```bash
python -m sp63_core portable-package --output-dir reports/portable_package_smoke --json
```

## Generated Skeleton

- `README_PORTABLE_PACKAGE.md`
- `INSTALL_WINDOWS.md`
- `RUN_CLEAN_DEMO.cmd`
- `RUN_PREFLIGHT.cmd`
- `RUN_WORKFLOW.cmd`
- `OPEN_REPORT_INDEX.cmd`
- `input/rectangular_input.json`
- `evidence/external_validation_template.csv`
- `evidence/material_verification_template.csv`
- `docs/quickstart.md`
- `docs/acceptance_checklist.md`
- `portable_manifest.json`

## Limits

- No exe is created.
- No PyInstaller bundle is created.
- No binary files are generated.
- No Streamlit, Gradio, PyQt, Tkinter, FastAPI, Flask, or Electron is added.
- Generated reports and smoke artifacts must not be committed.
