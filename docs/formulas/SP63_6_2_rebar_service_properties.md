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
- A400: Rsser = 390 MPa
- A500: Rsser = 500 MPa

## Limitations

- Values must be checked against SP 63 tables by an engineer.
- ML does not use Rsser directly in K15.
- Strength formulas are not changed by this card.

## Step 3 source decision

`Rsser` is traced to clause 6.2.7 and table 6.13, not table 6.14. The attached
base PDF contains 400 MPa for A400 in table 6.13. The catalog value 390 MPa is
retained only from the Step 2 statement about Amendment 1 under provisional
profile `SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15`; that amendment artifact
is not present in the repository.

- Source status for the attached base row: `CONFIRMED` (400 MPa).
- Status of the implemented A400 value 390 MPa: `ASSUMPTION`.
- Amendment evidence and final disposition: `OPEN_QUESTION`.
- Architecture impact: one catalog row feeds all SLS consumers, so the value
  must not be promoted independently of the material evidence gate.
- Engineering verification: mandatory before release or project use.
