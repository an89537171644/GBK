# SP63 reinforcement service properties

requires_engineer_review = true

## Purpose

Draft-MVP reinforcement service property card for second limit-state checks.

## Scope

- non-prestressed reinforcement classes A240, A400, A500;
- serviceability checks only;
- values are draft catalog values and require engineer verification.

## Properties

- Rs is used for first limit-state strength checks.
- Rsser is used for second limit-state serviceability checks.
- For the current MVP, Rsser is accepted as the tensile normative resistance by
  reinforcement class.

## Draft values

- A240: Rsser = 240 MPa
- A400: Rsser = 400 MPa
- A500: Rsser = 500 MPa

## Limitations

- Values must be checked against SP 63 tables by an engineer.
- ML does not use Rsser directly in K15.
- Strength formulas are not changed by this card.
