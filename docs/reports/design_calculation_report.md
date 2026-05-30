# Design calculation report export

requires_engineer_review = true

## Purpose

K36 adds a draft calculation report export for rectangular reinforced concrete
beam design results produced by `design_rectangular_element()`.

The report is intended for engineering review and traceability. It is not a
certified design conclusion.

## Available commands

```bash
python -m sp63_core design-report --markdown
python -m sp63_core design-report --html
python -m sp63_core design-report --json
python -m sp63_core design-report --markdown --output reports/rectangular_design_report.md
```

The K36 CLI uses a built-in rectangular beam smoke example with bending, shear,
normal crack formation, crack width, and deflection checks enabled.

K37 adds input-driven report generation:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --html
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The input JSON schema is documented in
`docs/reports/design_report_input_schema.md`. The built-in K36 smoke mode is
preserved when `--input-json` is omitted.

## Report sections

- input data;
- geometry;
- concrete and reinforcement materials;
- selected longitudinal reinforcement;
- selected transverse reinforcement;
- bending check;
- shear check;
- serviceability checks when requested;
- final strength, serviceability, and overall statuses;
- warnings;
- limitations.

## JSON structure

The JSON report includes:

- `report_type = "rectangular_design_calculation_report"`;
- status fields;
- `requires_engineer_review = true`;
- input data;
- materials;
- geometry;
- reinforcement;
- checks;
- warnings;
- limitations.

The existing `CalculationProtocol.as_dict()` structure is preserved and is
included as a nested `protocol` value for traceability.

For `--input-json`, the CLI JSON output also includes:

- `command = "design-report"`;
- `source = "input_json"`;
- top-level report status fields;
- top-level `input_data`, `materials`, `geometry`, `reinforcement`, and
  `checks` blocks.

## Limitations

- rectangular beam draft-MVP only;
- not a certified calculation conclusion;
- material verification remains a separate engineer-reviewed gate;
- external validation remains a separate engineer-reviewed gate;
- full SP 63 text is not stored in the repository;
- ML and neural surrogate outputs remain advisory-only;
- deterministic SP63 checks remain mandatory.
- input-driven reports still require engineer review and do not certify a
  project design.
