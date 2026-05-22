# SP63 6.2.8 - reinforcement compression resistance Rsc by load duration

requires_engineer_review = true

## Scope

MVP support for A240, A400, and A500 reinforcement.

## Rule

Rsc is selected by load duration.

For A500:
- long: 435 MPa
- short: 400 MPa

For A240 and A400:
- long and short values are equal in the MVP catalog.

## Implementation

Use `rebar.get_Rsc(load_duration)`.

`Rsc_override` has priority over `load_duration` for manual review cases.

## Units

MPa = N/mm2.
