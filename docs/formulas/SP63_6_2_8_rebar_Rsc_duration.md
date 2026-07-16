# SP63 6.2.8 - reinforcement compression resistance Rsc by load context

requires_engineer_review = true

## Scope

The material catalog contains A240, A400, and A500. The provisional longitudinal
ULS resolver accepts only A400 and A500 under provisional profile
`SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15`.

A240 remains available for transverse reinforcement and legacy catalog
consumers; passing it as longitudinal ULS reinforcement returns
`outside_applicability`.

## Rule

The applied `Rsc` is selected from the declared load context.

For A500:
- long: 435 MPa
- short: 400 MPa

For A240:
- long and short: 210 MPa

For A400:
- long and short: 340 MPa

## Implementation

Use `resolve_uls_material_context(concrete, rebar, load_duration)` for the
provisional ULS path. The resolver records the selected combination, normative
profile, applied concrete factor, effective `Rb`, and `Rsc` together.

An arbitrary `Rsc_override` is not an approved project-mode source of material
resistance.

## Traceability

- Source: SP 63.13330.2018, clause 6.2.8 and table 6.14. The attached base PDF
  contains A400 `Rs/Rsc = 350/350 MPa`; Step 2 attributes the implemented
  340/340 MPa row to Amendment 1, whose artifact is not attached.
- Source status: base row `CONFIRMED`; implemented A400 340 MPa
  `ASSUMPTION`; Amendment 1 evidence `OPEN_QUESTION`.
- Architecture impact: one centralized resolver; no independent duration
  interpretation inside calculation modules.
- Engineering verification: required before release and project use; the
  provisional A400 row cannot close the material gate.

## Units

MPa = N/mm2.
