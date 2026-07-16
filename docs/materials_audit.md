# Material Catalog Audit

## Purpose

The material catalog stores MVP values used by the deterministic `sp63_core`
calculation modules. The Step 3 corrections listed below use provisional profile
`SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15`, but they are not a signed engineering
approval for project design. All values retain the
`requires_engineer_review = true` gate.

The full text of SP 63 is not stored in this repository.

## Usage In The Core

Concrete strength properties for the first limit state:

- `Rb` - concrete compression resistance.
- `Rbt` - concrete tension resistance.

Concrete serviceability properties:

- `Rbser` - service concrete compression resistance.
- `Rbtser` - service concrete tension resistance.

Concrete stiffness:

- `Eb` - concrete elastic modulus.

Reinforcement strength and service properties:

- `Rsn` - normative reinforcement tensile strength.
- `Rs` - first limit-state reinforcement tension resistance.
- `Rsser` - service limit-state reinforcement tension resistance.
- `Rsc_short` - short-term compression reinforcement resistance.
- `Rsc_long` - long-term compression reinforcement resistance.
- `Rsw` - transverse reinforcement resistance.
- `Es` - reinforcement elastic modulus.

ML is advisory-only. It must not treat these material values as final approved
normative values, and every ML proposal must be checked by deterministic
`sp63_core`.

## Supported Concrete Classes

Heavy concrete MVP classes: B15, B20, B25, B30, B35, B40.

| class_name | Rb | Rbt | Rbser | Rbtser | Eb | audit_status | requires_engineer_review |
|---|---:|---:|---:|---:|---:|---|---|
| B15 | 8.5 | 0.75 | 11.0 | 1.10 | 24000 | draft_requires_engineer_review | true |
| B20 | 11.5 | 0.90 | 15.0 | 1.35 | 27500 | draft_requires_engineer_review | true |
| B25 | 14.5 | 1.05 | 18.5 | 1.55 | 30000 | draft_requires_engineer_review | true |
| B30 | 17.0 | 1.15 | 22.0 | 1.75 | 32500 | draft_requires_engineer_review | true |
| B35 | 19.5 | 1.30 | 25.5 | 1.95 | 34500 | draft_requires_engineer_review | true |
| B40 | 22.0 | 1.40 | 29.0 | 2.10 | 36000 | draft_requires_engineer_review | true |

## Supported Reinforcement Classes

MVP reinforcement classes: A240, A400, A500.

| class_name | Rsn | Rs | Rsser | Rsc_short | Rsc_long | Rsw | Es | audit_status | requires_engineer_review |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| A240 | 240 | 210 | 240 | 210 | 210 | 170 | 200000 | draft_requires_engineer_review | true |
| A400 | 390 | 340 | 390 | 340 | 340 | 280 | 200000 | draft_requires_engineer_review | true |
| A500 | 500 | 435 | 500 | 400 | 435 | 300 | 200000 | draft_requires_engineer_review | true |

## Properties Requiring Manual Review

All listed material values require manual engineering verification:

- concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb`;
- reinforcement `Rsn`, `Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es`.

Possible discrepancies must be resolved by an engineer before the values are
used in final design decisions.

## Step 3 Rechecked And Provisional Rows

| Catalog row | Source | Status | Architecture impact | Engineering check |
|---|---|---|---|---|
| B15 `Rbtser = 1.10 MPa` | SP 63.13330.2018, table 6.7; profile `SP63-2018-AMD1-AMD2-PROVISIONAL@2026-07-15` | `CONFIRMED` against the attached base edition | service checks read the rechecked catalog row | required before release |
| A400 `Rsn = 390 MPa`, `Rsser = 390 MPa` | Step 2 statement about clause 6.2.7/table 6.13 in Amendment 1; attached base PDF table 6.13 contains 400 MPa | implemented values `ASSUMPTION`; Amendment evidence `OPEN_QUESTION` | all A400 normative/service tensile consumers use one provisional catalog row | required before release |
| A400 `Rs = 340 MPa`, `Rsc = 340 MPa` | Step 2 statement about clause 6.2.8/table 6.14 in Amendment 1; attached base PDF table 6.14 contains 350 MPa | implemented values `ASSUMPTION`; Amendment evidence `OPEN_QUESTION` | all A400 ULS tension/compression consumers use one provisional catalog row | required before release |

The two machine keys `Rsc_short` and `Rsc_long` both store 340 MPa for A400.
They represent one applied `Rsc` selected by the declared load combination,
not two different normative symbols.

No durable local artifacts or hashes for Amendments 1 and 2, and no engineer
sign-off for the combined profile, are stored in the repository. Amendment-
dependent A400 provenance therefore remains `OPEN_QUESTION` / evidence pending
even though the provisional rows are retained for regression and review.

## ULS Material Context

`resolve_uls_material_context(...)` is the single material resolver for the
provisional ULS path. It returns the profile identifier, the closed load-combination
key, base and effective `Rb`, applied `gamma_b1`, selected `Rsc`, exact source
clauses, and the engineering-review gate. The key `short` means that the
combination contains short-term loads; `long` means only permanent and
long-term loads. No unspecified third state is accepted.

## K34 Engineer Verification Gate

K34 adds a separate verification gate for material catalog values.

Allowed verification statuses:

- `draft` - the catalog value is present but not checked yet;
- `needs_review` - the value or source note needs additional engineering review;
- `engineer_verified` - an engineer checked the value against SP 63 tables.

The gate does not change material values automatically. If an engineer-filled
CSV has a value that differs from the current catalog value, the row remains
`needs_review` until the discrepancy is resolved by an engineer.

Templates:

The repository sample `tests/fixtures/material_verification_sample.csv` is
synthetic test data and is not evidence. Step 3 rechecked/provisional rows are kept as
`needs_review` without a reviewer name or review date; only a separately
engineer-filled CSV may close this gate.

- `docs/materials/templates/material_catalog_verification_template.csv`;
- `docs/materials/material_catalog_engineer_verification.md`.

CLI:

```bash
python -m sp63_core materials-audit --verification-template
python -m sp63_core materials-audit --verification-csv path/to/material_verification.csv --json
python -m sp63_core material-verification --json
python -m sp63_core material-verification --template
python -m sp63_core material-verification --csv path/to/material_verification.csv --json
```

Rows marked `engineer_verified` must include:

- `engineer_value` matching the current catalog value;
- `engineer_name`;
- `review_date`;
- `source_note`.

## K35 Report Integration

K35 adds a Markdown/JSON report command for engineer-filled CSV files:

```bash
python -m sp63_core material-verification-report --csv path/to/material_verification.csv
python -m sp63_core material-verification-report --csv path/to/material_verification.csv --json
python -m sp63_core material-verification-report --csv path/to/material_verification.csv --output reports/material_verification_report.md
```

The report includes:

- `total_rows`;
- `engineer_verified_count`;
- `needs_review_count`;
- `missing_required_fields_count`;
- a table of rows that still need review.

The report is read-only. It does not update `materials/concrete.py`,
`materials/rebar.py`, or any calculation formula.
