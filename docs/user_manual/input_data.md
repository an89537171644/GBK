# Input Data

Input JSON files must use documented fields from `input-form-schema`.

Required beam inputs include geometry, material classes, and load effects:

- `b`;
- `h`;
- `cover`;
- `stirrup_diameter_for_geometry`;
- `concrete_class`;
- `longitudinal_rebar_class`;
- `stirrup_rebar_class`;
- `M`;
- `Q`.

Serviceability fields such as `Mser`, `span`, `check_cracks`,
`check_crack_width`, and `check_deflection` are optional and must be reviewed
by an engineer.

`ml_ready_for_project_use` must not be user supplied and must remain false.
