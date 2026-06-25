# Input Form Schema

requires_engineer_review = true

K66 adds a machine-readable schema for a future engineering input form:

```bash
python -m sp63_core input-form-schema --output-dir reports/input_form_schema --json
```

The schema is metadata only. It does not implement a GUI, start a server, run
calculations, approve ML for project use, or replace deterministic SP63 checks.

## Output Files

When an output directory is provided, the command writes:

- `input_form_schema.json`;
- `input_form_schema.md`.

Both files keep:

- `requires_engineer_review = true`;
- `ml_is_advisory_only = true`;
- `deterministic_checks_required = true`;
- `ml_ready_for_project_use = false`.

## Field Groups

The schema describes these groups:

- geometry: `b`, `h`, `cover`, `stirrup_diameter_for_geometry`, `span`;
- materials: `concrete_class`, `longitudinal_rebar_class`, `stirrup_rebar_class`;
- loads: `M`, `Q`, `Mser`;
- checks: `check_cracks`, `check_crack_width`, `check_deflection`, `acrc_limit`,
  `deflection_limit`, `deflection_limit_ratio`, `load_duration`;
- workflow: `output_dir`, `create_zip`, `with_index`, `include_ml_readiness`;
- optional ML-readiness inputs: `dataset_path`, `external_validation_csv`,
  `material_verification_csv`.

Every field includes a label, type, required flag, default or example, unit when
applicable, engineering hint, and validation message.

## Required Warning

```text
This schema is for future UI/input forms only. It does not perform design calculations and does not approve ML for project use.
```

Future UI layers must keep deterministic SP63 status, archive validation,
material verification, external validation, and engineer-review warnings visible.

## K67 Preflight Follow-Up

K67 turns the K66 schema and validation hints into an executable preflight
report:

```bash
python -m sp63_core input-preflight --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/input_preflight --json
```

The preflight command still does not calculate a design. It checks input JSON
shape and engineering sanity before workflow execution, writes JSON/Markdown
reports, and keeps `ml_ready_for_project_use = false`.
