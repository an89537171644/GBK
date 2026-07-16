# SP63 reinforcement service properties

requires_engineer_review = true
project_use = false

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

`Rsser` is traced to clause 6.2.7 and table 6.13, not table 6.14. The
user-provided scan of SP 63.13330.2018 with Amendments 1 and 2 has SHA-256
`8dfe7fc1af47d6adf2a4d91ed91ee92fe0762abe20a0c54b3c248c7ff138fe00`.
PDF page 2 confirms the stated amendment composition and dates; PDF pages
35-37 contain tables 6.13-6.15 for A240, A400, and A500.

- Artifact-content status for the listed service rows: `CONFIRMED`.
- Status of the implemented A400 value `Rsser = 390 MPa`: `CONFIRMED`
  against the reviewed artifact.
- Authenticity, legal status, and currentness beyond Amendment 2:
  `OPEN_QUESTION`.
- Architecture impact: one catalog row feeds all SLS consumers, so the value
  must not be promoted independently of the material evidence gate.
- Engineering verification: independent review is mandatory before release;
  this content confirmation does not approve formulas or project use.
