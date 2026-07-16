# Changelog

## Unreleased — ULS-BEND-RECT-001 step 3 remediation

- Confirmed the B15 service row and the A400 390/340 MPa rows against the
  content of the user-provided SP 63.13330.2018 scan with Amendments 1 and 2,
  SHA-256
  `8dfe7fc1af47d6adf2a4d91ed91ee92fe0762abe20a0c54b3c248c7ff138fe00`.
  This is content-level confirmation only: authenticity, legal status, and
  currentness beyond Amendment 2 remain an open question.
- Added an explicit ULS material/load context with `gamma_b1` provenance.
- Made local axes, bending axis, tension face, and load context mandatory inputs.
- Removed arbitrary `h0_override`, compression-diameter fallback, and `Rsc_override` paths.
- Restricted version 1 to `As_prime = 0` and stopped capacity output outside applicability.
- Added BMR-01—BMR-05 regression evidence and separate completeness/evidence/project statuses.
- Rebased the review branch onto K109 and recorded the intentional
  `protected-files-check` failure as a mandatory engineering merge gate rather
  than weakening the guard or its dependent audit checks.

The calculation branch remains subject to engineering review. Clause 8.1.3 is
not checked, BMR expected values remain `ASSUMPTION` pending independent
reproduction, external evidence is incomplete, and `project_use` remains
false.

## 0.9.0-rc1 engineering review preparation

- Added material verification closure workflow.
- Added clean deterministic demo workflow.
- Added portable engineering handoff package.
- Added lightweight launcher scripts package.
- Added external validation evidence package.
- Added aggregated v0.9 final audit.
- Added local agent sprint guard.
- Added v0.9 release notes, checklist, and known limitations package.

This changelog entry is release-preparation documentation only. It does not
publish a release, certify calculations, approve project use, or make ML
project-ready.
