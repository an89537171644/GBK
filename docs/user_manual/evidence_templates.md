# Evidence Templates

Create blank evidence templates for engineer handoff:

```bash
python -m sp63_core evidence-templates \
  --output-dir reports/evidence_templates \
  --json
```

The package includes external validation and material verification CSV
templates plus a README and SHA256 manifest.

## Material Verification Closure

After an engineer fills the material verification CSV, run:

```bash
python -m sp63_core material-verification-closure \
  --material-verification-csv path/to/material_verification.csv \
  --output-dir reports/material_verification_closure \
  --json
```

The closure report checks whether every required material property is covered
by `engineer_verified` rows. It can mark the material verification evidence as
ready for engineering review, but `material_ready_for_project_use` remains
`false` and the material catalog is not changed automatically.

Do not add full SP 63 text, personal data, grant documents, or closed SCAD/LIRA
files.
