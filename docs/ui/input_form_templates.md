# Input Form Templates

requires_engineer_review = true

K66 adds anonymized input-form examples under:

```text
docs/reports/examples/form_templates/
```

## Templates

- `rectangular_minimal_input_template.json` - minimum deterministic rectangular
  design-report input.
- `rectangular_serviceability_input_template.json` - rectangular input with
  crack formation, crack width, and deflection flags.
- `rectangular_ml_readiness_workflow_template.json` - future workflow-form
  values for report output, static index, and optional ML-readiness inputs.
- `rectangular_preflight_invalid_input.json` - anonymized invalid input used to
  demonstrate preflight `fail` output.
- `rectangular_preflight_review_input.json` - anonymized input used to
  demonstrate preflight `review_required` output.

The workflow template is a form example, not a direct `design-report
--input-json` payload. It may include workflow fields such as `output_dir`,
`with_index`, and `include_ml_readiness`.

## Privacy And Safety

The templates are synthetic and anonymized. They do not contain personal data,
grant data, private project documents, closed SCAD/LIRA files, or full SP63
text.

`ml_ready_for_project_use` is intentionally not an input template field. It is a
result/status flag and must remain false.

## K67 Preflight Usage

Use `input-preflight` to check direct rectangular design input templates before
running report/workflow commands:

```bash
python -m sp63_core input-preflight --input-json docs/reports/examples/form_templates/rectangular_serviceability_input_template.json --output-dir reports/input_preflight --json
```

The preflight examples are synthetic and intentionally limited to input
validation. They are not project calculations.
