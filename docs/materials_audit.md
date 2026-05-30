# Material Catalog Audit

## Purpose

The material catalog stores draft MVP values used by the deterministic
`sp63_core` calculation modules. These values are not certified project-design
values. They must be checked by an engineer against SP 63 material tables before
final use.

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
| B15 | 8.5 | 0.75 | 11.0 | 1.15 | 24000 | draft_requires_engineer_review | true |
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
| A400 | 400 | 350 | 400 | 350 | 350 | 280 | 200000 | draft_requires_engineer_review | true |
| A500 | 500 | 435 | 500 | 400 | 435 | 300 | 200000 | draft_requires_engineer_review | true |

## Properties Requiring Manual Review

All listed material values require manual engineering verification:

- concrete `Rb`, `Rbt`, `Rbser`, `Rbtser`, `Eb`;
- reinforcement `Rsn`, `Rs`, `Rsser`, `Rsc_short`, `Rsc_long`, `Rsw`, `Es`.

Possible discrepancies must be resolved by an engineer before the values are
used in final design decisions. K19 adds the audit structure only; it does not
approve or change material values.

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
