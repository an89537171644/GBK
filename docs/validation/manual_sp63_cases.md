# Manual SP63 Verification Cases

requires_engineer_review = true

## Purpose

K20 fixes six manual control calculations as a repeatable validation package for
the deterministic `sp63_core` draft-MVP calculation core.

The cases are based on `manual_sp63_verification_cases_K20.md`. They follow the
current MVP formula cards and are not a replacement for a complete normative
SP 63 design calculation. Material values, coefficients, serviceability checks,
and all conclusions still require engineering review.

Full SP 63 text is not included in this repository.

## Common Inputs

- Rectangular beam section: `b = 300 mm`, `h = 500 mm`.
- Cover: `32 mm`.
- Stirrup diameter for geometry: `8 mm`.
- Concrete: `B25`.
- Longitudinal reinforcement: `A500`.
- Transverse reinforcement: `A240`.

## Tolerances

| indicator | tolerance |
|---|---:|
| As, Asw | +/- 0.01 mm2 |
| x, xi, xi_R | +/- 0.5% draft comparison |
| Mult, Qult, Mcrc | +/- 1.0% draft comparison |
| acrc | +/- 0.005 mm |
| deflection | +/- 0.05 mm |
| strength_status, serviceability_status, overall_status | exact match |

## Case List

### Case 1 - Basic passing beam

Inputs:

- Longitudinal reinforcement: `3D20`, `As = 942.48 mm2`.
- Stirrups: `2D8`, `sw = 200 mm`, `Asw = 100.53 mm2`.
- `M = 150,000,000 N*mm`.
- `Q = 80,000 N`.
- `Mser = 30,000,000 N*mm`.
- `span = 6000 mm`, `deflection_limit = span / 250 = 24 mm`.

Expected status:

- `strength_status = pass`
- `serviceability_status = pass`
- `overall_status = pass`

Key expected values:

- `h0 = 450 mm`
- `Mult ~= 165.17 kN*m`
- `Qult ~= 163.99 kN`
- `Mcrc ~= 19.375 kN*m`
- `acrc ~= 0.157 mm`
- `deflection ~= 4.38 mm`

### Case 2 - Bending failure

Inputs:

- Longitudinal reinforcement: `2D16`, `As = 402.12 mm2`.
- `M = 150,000,000 N*mm`.

Expected status:

- `bending.status = fail`
- `strength_status = fail`
- `overall_status = fail`

Key expected values:

- `h0 = 452 mm`
- `Mult ~= 75.55 kN*m`
- `bending_utilization ~= 1.985`

### Case 3 - Crack formation without crack width check

Inputs:

- Same strength inputs as Case 1.
- `Mser = 30,000,000 N*mm`.
- Crack formation is checked, but crack width and deflection are not checked.

Expected status:

- `crack_formation.status = crack`
- `strength_status = pass`
- `serviceability_status = review_or_fail`
- `overall_status = review_or_fail`

### Case 4 - Crack width failure

Inputs:

- Longitudinal reinforcement: `2D16`, `As = 402.12 mm2`.
- `Mser = 90,000,000 N*mm`.
- `acrc_limit = 0.3 mm`.

Expected status:

- `crack_width.status = fail`
- `serviceability_status = fail`
- `overall_status = fail`

Key expected values:

- `sigma_s ~= 550.18 MPa`
- `acrc ~= 1.100 mm`
- `crack_width_utilization ~= 3.668`

Expected warnings:

- service reinforcement stress exceeds `Rsser`;
- crack width exceeds the draft limit.

### Case 5 - Deflection failure

Inputs:

- Longitudinal reinforcement: `2D16`, `As = 402.12 mm2`.
- `Mser = 80,000,000 N*mm`.
- `span = 12000 mm`.
- `deflection_limit = span / 250 = 48 mm`.

Expected status:

- `deflection.status = fail`
- `serviceability_status = fail`
- `overall_status = fail`

Key expected values:

- `Icracked ~= 422,131,603 mm4`
- `deflection ~= 94.76 mm`
- `deflection_utilization ~= 1.974`

### Case 6 - Shear failure

Inputs:

- Stirrups: `2D6`, `sw = 300 mm`, `Asw = 56.55 mm2`.
- `Q = 200,000 N`.

Expected status:

- `shear.status = fail`
- `strength_status = fail`
- `overall_status = fail`

Key expected values:

- `qsw ~= 32.04 N/mm`
- `Qult ~= 127.94 kN`
- `shear_utilization ~= 1.563`

Expected warning:

- `qsw` is below the draft minimum rule for counting transverse reinforcement.

## CLI

Run:

```bash
python -m sp63_core manual-cases --json
```

Expected summary:

- `status = pass`
- `case_count = 6`
- `passed_count = 6`
- every case has `requires_engineer_review = true`
