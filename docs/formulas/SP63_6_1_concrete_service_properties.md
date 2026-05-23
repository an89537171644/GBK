# SP63 Concrete Service Properties

requires_engineer_review = true

## Purpose

This card records service material properties for future second limit-state
checks in the SP 63 MVP.

## Property Groups

- `Rb` and `Rbt` are used for first limit-state strength checks.
- `Rbser` and `Rbtser` are used for second limit-state service checks.
- `Eb` is the concrete elastic modulus.

## MVP Scope

- Heavy concrete only.
- Classes B15-B40 only.
- Values are stored in `src/sp63_core/materials/concrete.py`.

## Source

The values must be checked by an engineer against SP 63 concrete resistance
tables before crack or deflection calculations are accepted.

## Limits

K13 only adds material properties. Crack formation, crack width, and deflection
checks are not implemented yet.
