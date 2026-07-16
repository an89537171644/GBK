# SP63 6.2.8 - reinforcement compression resistance Rsc by load context

requires_engineer_review = true
project_use = false

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

- Source artifact: user-provided scan of SP 63.13330.2018 with Amendments 1
  and 2, SHA-256
  `8dfe7fc1af47d6adf2a4d91ed91ee92fe0762abe20a0c54b3c248c7ff138fe00`;
  PDF page 2 confirms the stated amendment composition and dates.
- Source: clause 6.2.8 and table 6.14, reviewed on PDF pages 35-37.
- Artifact-content status: the implemented A400 `Rs/Rsc = 340/340 MPa` row
  is `CONFIRMED` against this artifact.
- Evidence boundary: authenticity, legal status, and currentness beyond
  Amendment 2 remain `OPEN_QUESTION`.
- Architecture impact: one centralized resolver; no independent duration
  interpretation inside calculation modules.
- Engineering verification: independent review is required before release;
  artifact-content confirmation alone cannot close the material gate or
  approve project use.

## Units

MPa = N/mm2.
