# Design report input schema

requires_engineer_review = true

## Purpose

K37 allows `design-report` to build a rectangular beam calculation report from
an input JSON file. The input creates `RectangularDesignInput`, runs the
existing deterministic design workflow, and renders the K36 report formats.

This is an input/reporting layer only. It does not change formulas,
reinforcement selection algorithms, material values, or ML behavior.

## Example

```json
{
  "b": 300,
  "h": 500,
  "cover": 32,
  "stirrup_diameter_for_geometry": 8,
  "concrete_class": "B25",
  "longitudinal_rebar_class": "A500",
  "stirrup_rebar_class": "A240",
  "M": 150000000,
  "Q": 80000,
  "local_axes_id": "example-section-local-axes",
  "moment_axis": "local_z",
  "tension_face": "local_y_min",
  "load_duration": "short",
  "Mser": 30000000,
  "check_cracks": true,
  "check_crack_width": true,
  "check_deflection": true,
  "span": 6000,
  "acrc_limit": 0.3,
  "deflection_limit_ratio": 250
}
```

The same example is stored in
`docs/reports/examples/rectangular_design_input_example.json`.

## Required fields

| field | unit | meaning |
|---|---|---|
| `b` | mm | rectangular section width |
| `h` | mm | rectangular section height |
| `cover` | mm | distance from the concrete face to the outer stirrup surface in the current single-row geometry |
| `stirrup_diameter_for_geometry` | mm | stirrup diameter used for effective depth geometry |
| `concrete_class` | text | concrete class from the draft catalog |
| `longitudinal_rebar_class` | text | longitudinal reinforcement class |
| `stirrup_rebar_class` | text | transverse reinforcement class |
| `M` | N*mm | design bending moment |
| `Q` | N | design shear force |
| `local_axes_id` | text | non-empty identifier of the declared section-local axes |
| `moment_axis` | text | `local_z` for the current version |
| `tension_face` | text | explicit `local_y_min` or `local_y_max`; never inferred from moment sign |
| `load_duration` | text | `short` for the end-to-end report/design workflow |

## Optional fields

| field | unit | meaning |
|---|---|---|
| `Mser` | N*mm | service bending moment |
| `check_cracks` | bool | run normal crack formation check |
| `check_crack_width` | bool | run draft normal crack width check |
| `check_deflection` | bool | run draft deflection check |
| `span` | mm | beam span for deflection check |
| `acrc_limit` | mm | draft crack width limit |
| `deflection_limit` | mm | explicit deflection limit |
| `deflection_limit_ratio` | dimensionless | span divisor for default deflection limit |

## Units

- dimensions: mm;
- moments: N*mm;
- forces: N;
- areas in output: mm2;
- stresses and moduli: MPa.

## Validation rules

- Missing required fields raise a clear `ValueError`.
- Unknown fields are rejected instead of being silently accepted.
- The end-to-end design/report workflow accepts only `load_duration=short`.
  The isolated bending check has a separately verified provisional `long`
  branch; shear and the full workflow do not propagate that context and return
  `outside_applicability`.
- This loader does not define or approve calculation formulas; it passes the
  validated contract to the deterministic workflow.
- All generated reports keep `completeness_status=incomplete`,
  `evidence_status=needs_engineer_review`, `project_use_status=prohibited`,
  `project_use=false`, and `requires_engineer_review=true`.

## CLI

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --html
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The bundle output writes `report.md`, `report.json`, `report.html`, a copy of
the source `input.json`, and `manifest.json` for traceability.

Without `--input-json`, the K36 built-in smoke example remains available.
