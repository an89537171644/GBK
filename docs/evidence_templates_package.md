# Evidence Templates Package

requires_engineer_review = true

## Purpose

K72 packages the existing external validation and material verification CSV
templates into a single engineer handoff folder. The package helps collect
manual/Excel/SCAD/LIRA comparison values and material catalog verification
evidence without changing the deterministic calculation core.

The package does not include real external values, closed SCAD/LIRA files,
personal data, grant documents, or full SP 63 text.

## CLI

```bash
python -m sp63_core evidence-templates \
  --output-dir reports/evidence_templates \
  --json
```

## Output Structure

```text
reports/evidence_templates/
  external_validation_template.csv
  material_verification_template.csv
  README_EVIDENCE_TEMPLATES.md
  evidence_templates_manifest.json
```

The manifest includes SHA256 checksums for generated files.

## Engineer Workflow

1. Fill `external_validation_template.csv` with engineer-reviewed manual,
   Excel, SCAD, or LIRA comparison values.
2. Fill `material_verification_template.csv` after checking material values
   against SP 63 tables.
3. Do not paste full normative text into the repository.
4. Do not add personal, grant, private, or closed SCAD/LIRA documents.
5. Run the external validation and material verification commands after filling
   the templates.

## Safety

- Templates do not certify designs.
- Material verification does not automatically update the catalog.
- ML remains advisory-only.
- Deterministic SP63 checks remain mandatory.
- Engineer review remains mandatory.
- `ml_ready_for_project_use` remains false.
