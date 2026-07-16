# SP63 Concrete Service Properties

requires_engineer_review = true

## Purpose

This card records service material properties used by the draft second
limit-state checks in the SP 63 MVP.

## Property Groups

- `Rb` and `Rbt` are used for first limit-state strength checks.
- `Rbser` and `Rbtser` are used for second limit-state service checks.
- `Eb` is the concrete elastic modulus.

## MVP Scope

- Heavy concrete only.
- Classes B15-B40 only.
- Values are stored in `src/sp63_core/materials/concrete.py`.

## Step 3 base-PDF recheck

- B15: `Rbtser = 1.10 MPa`.
- Source: SP 63.13330.2018, table 6.7, provisional profile
  `SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15`.
- Source status: `CONFIRMED`.
- Architecture impact: all serviceability consumers read the rechecked value
  from the common concrete catalog.
- Engineering verification: required before release and project use.

## Source

The values must be checked by an engineer against SP 63 concrete resistance
tables before crack or deflection calculations are accepted.

## Limits

Draft crack formation, crack width, curvature, and deflection checks are
implemented, but they are not independently validated or approved for project
use. Their formula cards, assumptions, and applicability still require
engineering review.
