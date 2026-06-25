# K78 Project Template Package

K78 adds `project-template`, a portable folder scaffold for starting an
engineering review package.

```bash
python -m sp63_core project-template \
  --output-dir reports/project_template_smoke \
  --json
```

The package contains:

- `input/rectangular_input.json`;
- `evidence/external_validation_template.csv`;
- `evidence/material_verification_template.csv`;
- `README_PROJECT_TEMPLATE.md`;
- `RUN_COMMANDS.md`;
- `acceptance_checklist.md`;
- `project_template_manifest.json`.

`project_template_manifest.json` records SHA256 checksums for generated files.

The package is a handoff scaffold only. It does not run calculations, certify
designs, update material values, include full SP 63 text, include personal or
closed SCAD/LIRA files, or make ML project-ready.

Deterministic SP63 checks and engineer review remain mandatory.
