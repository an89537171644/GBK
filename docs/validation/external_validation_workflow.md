# External validation workflow

requires_engineer_review = true

## Purpose

K31 prepares the external engineering validation workflow for comparing
`sp63_core` draft-MVP results with independent manual calculations, SCAD, LIRA,
or engineer-maintained Excel templates.

This workflow is a control layer. It does not change formulas and does not
certify the program.

## Compared Results

The external validation template records program and external values for:

- bending capacity;
- shear capacity;
- normal crack formation moment;
- normal crack width;
- deflection;
- separated strength, serviceability, and overall statuses.

The K20 manual verification cases are already available as an internal manual
check set. K31 adds the structure for external values that must be filled by an
engineer.

## Engineer Responsibilities

An engineer must fill the SCAD, LIRA, manual, or Excel comparison values in:

`docs/validation/templates/external_validation_cases_template.csv`

The repository intentionally does not contain closed SCAD/LIRA files, private
calculation files, or full normative text. Only comparison fields and summary
logic are stored.

## Draft Status

Until external validation is filled and reviewed, the calculation core remains a
draft-MVP. Passing golden cases, manual cases, and dataset checks is useful but
does not replace external engineering validation.

## ML Safety

ML and neural surrogate outputs are not calculation results. They remain
advisory-only, and deterministic SP63 checks remain mandatory for every ML
proposal.

## CLI

Show the template path:

```bash
python -m sp63_core external-validation --template
```

Summarize a filled CSV:

```bash
python -m sp63_core external-validation --csv path/to/external_validation.csv --json
```

If external values are missing, the summary status is `review_required`.
