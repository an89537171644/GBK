# Input Preflight Report

requires_engineer_review = true

The K67 preflight report is a small engineering validation package generated
from an input JSON file:

```bash
python -m sp63_core input-preflight \
  --input-json docs/reports/examples/form_templates/rectangular_serviceability_input_template.json \
  --output-dir reports/input_preflight_markdown \
  --markdown
```

## Report Contents

The JSON and Markdown reports include:

- `status` and `preflight_status`;
- input JSON path and output directory;
- checked fields;
- required and optional fields;
- missing required fields;
- unknown fields;
- per-field issues with severity and engineering hint;
- safety flags.

## Intended Use

The report is meant for:

- CLI-first engineering workflows;
- future static HTML report viewers;
- future desktop wrappers or launchers;
- archive/review packages where engineers need to see input health before
  deterministic calculation output.

## Limitations

- The report does not run bending, shear, crack, crack-width, or deflection
  checks.
- The report does not approve material catalog values.
- The report does not approve external validation.
- The report does not make ML project-ready.
- Engineer review remains mandatory.
