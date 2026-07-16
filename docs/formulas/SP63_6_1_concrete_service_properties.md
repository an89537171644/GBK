# SP63 Concrete Service Properties

requires_engineer_review = true
project_use = false

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

## Step 3 artifact-content recheck

- B15: `Rbtser = 1.10 MPa`.
- Source artifact: user-provided scan of SP 63.13330.2018 with Amendments 1
  and 2, SHA-256
  `8dfe7fc1af47d6adf2a4d91ed91ee92fe0762abe20a0c54b3c248c7ff138fe00`;
  PDF page 2 confirms the stated amendment composition and dates.
- Reviewed source locations: table 6.7 on PDF page 24, table 6.8 on page 26,
  and table 6.11 on page 29.
- Artifact-content status: `CONFIRMED` for the concrete catalog values
  checked against those tables.
- Evidence boundary: authenticity, legal status, and currentness beyond
  Amendment 2 remain `OPEN_QUESTION`.
- Architecture impact: all serviceability consumers read the rechecked value
  from the common concrete catalog.
- Engineering verification: independent review is required before release;
  artifact-content confirmation does not approve calculations or project use.

## Source

The values must be checked by an engineer against SP 63 concrete resistance
tables before crack or deflection calculations are accepted.

## Limits

Draft crack formation, crack width, curvature, and deflection checks are
implemented, but they are not independently validated or approved for project
use. Their formula cards, assumptions, and applicability still require
engineering review.
