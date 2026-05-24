# SP63 8.2 normal crack width for rectangular section

requires_engineer_review = true

## Purpose

Draft-MVP normal crack width check for a rectangular reinforced concrete beam.

## Scope

- rectangular section;
- bending only;
- no axial force;
- no prestress;
- heavy concrete B15-B40;
- non-prestressed reinforcement A400/A500;
- normal crack width only.

## Units

- b, h, h0, z, crack_spacing - mm;
- Mser, Mcrc - N*mm;
- As - mm2;
- sigma_s, Rsser, Es - MPa = N/mm2;
- acrc, acrc_limit - mm.

## Draft formula

First check normal crack formation. If normal cracks are not expected:

acrc = 0

status = "not_required"

If normal cracks are expected:

h0 = section.effective_depth()

z = 0.9 * h0

sigma_s = Mser / (As * z)

epsilon_s = sigma_s / Es

rho_eff = As / (b * h0)

rho_eff_used = max(rho_eff, 0.001)

raw_crack_spacing = 0.5 * main_bar_diameter / rho_eff_used

crack_spacing = min(max(raw_crack_spacing, 100), 400)

acrc = epsilon_s * crack_spacing

utilization = acrc / acrc_limit

status:

- "pass" if acrc <= acrc_limit
- "fail" if acrc > acrc_limit

## Warnings

Always warn that this is a draft crack width check and that refined SP 63 crack
spacing and tension stiffening are not implemented.

Add a warning when `sigma_s > Rsser`.

Add a warning when `acrc > acrc_limit`.

## Outputs

- Mser
- Mcrc
- acrc
- acrc_limit
- utilization
- sigma_s
- epsilon_s
- crack_spacing
- status
- warnings
- intermediate_values
- requires_engineer_review = true

## Limitations

- refined SP 63 crack spacing is not implemented;
- tension stiffening is not implemented;
- long-term effects are not implemented;
- nonlinear deformation model is not implemented;
- transformed section is not implemented;
- deflection is not implemented.
