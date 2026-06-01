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

The workflow template is a form example, not a direct `design-report
--input-json` payload. It may include workflow fields such as `output_dir`,
`with_index`, and `include_ml_readiness`.

## Privacy And Safety

The templates are synthetic and anonymized. They do not contain personal data,
grant data, private project documents, closed SCAD/LIRA files, or full SP63
text.

`ml_ready_for_project_use` is intentionally not an input template field. It is a
result/status flag and must remain false.
