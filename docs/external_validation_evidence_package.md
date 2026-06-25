# K87 External Validation Evidence Package

K87 adds a package for external validation evidence handoff.

Create the package without a CSV:

```bash
python -m sp63_core external-validation-evidence-package --output-dir reports/external_validation_evidence_smoke --json
```

The command writes:

- `external_validation_engineer_input_template.csv`;
- `external_validation_engineer_checklist.md`;
- `external_validation_evidence_summary.json`;
- `external_validation_evidence_summary.md`;
- `external_validation_evidence_manifest.json`.

Without an engineer-filled CSV the expected status is `review_required`.

Summarize an engineer-filled CSV:

```bash
python -m sp63_core external-validation-evidence-package \
  --output-dir reports/external_validation_evidence_smoke \
  --external-validation-csv docs/validation/samples/external_validation_filled_sample.csv \
  --strict \
  --json
```

K87 does not change formulas, material values, protected calculation files, or
`validation/external.py`. It does not add real SCAD/LIRA files or full SP 63
text. External validation remains an engineer-filled evidence workflow.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
