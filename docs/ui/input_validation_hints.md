# Input Validation Hints

requires_engineer_review = true

K66 validation hints are UI/form guidance only. They do not change the
deterministic calculation core and do not replace the existing Python validation
inside `sp63_core`.

## Geometry

- Dimensions must be positive.
- `h > cover`.
- `cover < h`.
- `span > h` when span is provided.
- Effective depth must remain physically meaningful.

## Loads And Service Values

- `M >= 0`.
- `Q >= 0`.
- `Mser >= 0`.
- Current input convention expects `Mser <= M` when both values are provided.

## Materials

- `concrete_class` must exist in the material catalog.
- `longitudinal_rebar_class` must exist in the material catalog.
- `stirrup_rebar_class` must exist in the material catalog.
- Material catalog values still require engineer verification.

## ML Readiness Inputs

- `dataset_path` is required when `include_ml_readiness = true`.
- `external_validation_csv` must exist when provided.
- `material_verification_csv` must exist when provided.
- `ml_ready_for_project_use` must not be user-settable and must remain false.

## Safety

The future form must never show advisory ML output as a design decision. Any UI
or wrapper must keep deterministic SP63 verification and engineer review
visually primary.

## K67 Executable Preflight

K67 adds `input-preflight` as an executable report over these hints:

```bash
python -m sp63_core input-preflight --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/input_preflight --json
```

Preflight can return `pass`, `review_required`, or `fail` before the engineering
workflow starts. It is still not a calculation and does not approve project
use.

## K68 Static Preview

K68 adds `input-form-preview`, which renders these fields and hints as static
HTML. The preview is safe to open as a file and contains no JavaScript
calculation logic.
