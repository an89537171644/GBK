# Evidence Templates

Create blank evidence templates for engineer handoff:

```bash
python -m sp63_core evidence-templates \
  --output-dir reports/evidence_templates \
  --json
```

The package includes external validation and material verification CSV
templates plus a README and SHA256 manifest.

Do not add full SP 63 text, personal data, grant documents, or closed SCAD/LIRA
files.
