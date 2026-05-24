# SP63 8.2 curvature and deflection for rectangular section

requires_engineer_review = true

Clause reference: SP 63 section 8.2, curvature and deflection.

## Purpose

Draft-MVP short-term curvature and deflection check for a rectangular
reinforced concrete beam.

## Scope

- rectangular section;
- bending only;
- no axial force;
- no prestress;
- heavy concrete B15-B40;
- non-prestressed reinforcement A400/A500;
- short-term draft curvature and deflection only;
- loading scheme `simply_supported_uniform` only.

## Units

- b, h, h0, span, deflection, deflection_limit - mm;
- Mser and Mcrc - N*mm;
- As - mm2;
- Eb and Es - MPa = N/mm2;
- I_gross, I_cracked, I_eff - mm4;
- curvature - 1/mm.

## Draft formulas

First check normal crack formation using the existing K14 draft check.

Gross section:

I_gross = b * h^3 / 12

If normal cracks are not expected:

I_eff = I_gross

stiffness_status = "gross_uncracked"

If normal cracks are expected, use a simplified transformed cracked section
without tensile concrete:

n = Es / Eb

0.5 * b * x^2 + n * As * x - n * As * h0 = 0

Use the positive root for neutral axis depth x.

I_cracked = b * x^3 / 3 + n * As * (h0 - x)^2

I_eff = I_cracked

stiffness_status = "draft_cracked_transformed"

Curvature:

curvature = Mser / (Eb * I_eff)

For `simply_supported_uniform`, K16 treats Mser as the maximum span moment:

f = 5/48 * curvature * span^2

If `deflection_limit` is set, use it directly. Otherwise:

deflection_limit = span / deflection_limit_ratio

utilization = deflection / deflection_limit

status:

- "pass" if deflection <= deflection_limit
- "fail" if deflection > deflection_limit

## Warnings

Always warn that this is a draft deflection check and that refined SP 63
curvature, cracking, long-term effects, creep, shrinkage, and tension
stiffening are not implemented.

Add a warning when the simplified cracked transformed stiffness is used.

Add a warning when deflection exceeds the draft limit.

## Outputs

- Mser
- Mcrc
- span
- curvature
- deflection
- deflection_limit
- utilization
- I_gross
- I_cracked
- I_eff
- stiffness_status
- loading_scheme
- status
- warnings
- intermediate_values
- requires_engineer_review = true

## Limitations

- no long-term deflection;
- no creep;
- no shrinkage;
- no refined tension stiffening model;
- no nonlinear deformation model;
- no slabs, columns, T-sections, punching, torsion, anchorage, support zones,
  or bar curtailment;
- no Streamlit or UI behavior.
