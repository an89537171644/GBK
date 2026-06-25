# Preflight Validation

Use input preflight before report generation:

```bash
python -m sp63_core input-preflight \
  --input-json docs/reports/examples/rectangular_design_input_example.json \
  --output-dir reports/input_preflight \
  --json
```

Preflight checks JSON shape, required fields, unknown fields, numeric ranges,
material class names, and workflow path hints.

Preflight does not run calculations and does not certify the input.
