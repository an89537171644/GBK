# Static Input Form Preview

requires_engineer_review = true

K68 adds a static HTML preview generated from the K66 input form schema:

```bash
python -m sp63_core input-form-preview --output-dir reports/input_form_preview --json
```

The preview is not a GUI, not a web app, and not a calculator. It displays
field groups, labels, units, required flags, defaults, min/max values,
engineering hints, validation messages, and mandatory safety warnings.

## Output Files

When `--output-dir` is provided, the command writes:

- `input_form_preview.html`;
- `input_form_preview.json`;
- `README_INPUT_FORM_PREVIEW.md`.

## HTML Safety

The preview contains:

- the warning that deterministic SP63 verification and engineer review are
  mandatory;
- `ml_ready_for_project_use = false`;
- field groups for geometry, materials, loads/internal forces, serviceability
  checks, workflow, and optional ML-readiness;
- no JavaScript calculation logic;
- no web server requirement;
- no `Approve design` action.

## Limitations

- Calculations are performed only through deterministic workflow commands.
- The preview does not certify input data.
- Material verification and external validation remain separate gates.
- ML remains advisory-only.
