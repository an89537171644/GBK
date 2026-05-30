# Material Catalog Engineer Verification Template

requires_engineer_review = true

## Purpose

This template is used to record engineer verification of material catalog
values used by `sp63_core`.

K34 does not approve or change material values automatically. It only adds a
gate for recording whether each value is still draft, needs review, or has
been engineer-verified.

## Verification Status Values

- `draft` - current catalog value has not been checked yet.
- `needs_review` - value or source note requires additional engineering review.
- `engineer_verified` - engineer checked the catalog value against SP 63 tables.

## Concrete Properties

| material_type | class_name | property_name | catalog_value | unit | verification_status | engineer_value | engineer_name | review_date | source_note | engineer_comment | requires_engineer_review |
|---|---|---|---:|---|---|---:|---|---|---|---|---|
| concrete | B25 | Rb | 14.5 | MPa | draft |  |  |  |  |  | true |

Concrete properties to verify:

- `Rb`
- `Rbt`
- `Rbser`
- `Rbtser`
- `Eb`

## Reinforcement Properties

| material_type | class_name | property_name | catalog_value | unit | verification_status | engineer_value | engineer_name | review_date | source_note | engineer_comment | requires_engineer_review |
|---|---|---|---:|---|---|---:|---|---|---|---|---|
| rebar | A500 | Rs | 435 | MPa | draft |  |  |  |  |  | true |

Reinforcement properties to verify:

- `Rsn`
- `Rs`
- `Rsser`
- `Rsc_short`
- `Rsc_long`
- `Rsw`
- `Es`

## Rules

- Do not paste full SP 63 text into this repository.
- Do not commit scans, licensed PDFs, or closed working files.
- Do not commit personal, grant, signature, phone, or private documents.
- If the engineer value differs from the catalog value, keep
  `verification_status = needs_review` until the difference is resolved.
- `engineer_verified` requires a filled `engineer_value` matching the current
  catalog value plus `engineer_name`, `review_date`, and a short `source_note`.

## CLI

Use the CSV template:

```bash
python -m sp63_core material-verification --template
```

Check current draft status:

```bash
python -m sp63_core material-verification --json
```

Check an engineer-filled CSV:

```bash
python -m sp63_core material-verification --csv path/to/material_verification.csv --json
```
