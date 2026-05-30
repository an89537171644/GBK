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

Run strict acceptance gate checks for engineer-filled real-data intake:

```bash
python -m sp63_core external-validation --csv path/to/engineer_filled.csv --strict --json
```

Run the public synthetic/manual sample:

```bash
python -m sp63_core external-validation --sample --json
```

## K32 Filled Sample

K32 adds:

`docs/validation/samples/external_validation_filled_sample.csv`

The sample contains six K20-aligned cases:

- base pass beam;
- bending fail;
- crack review without width;
- crack width fail;
- deflection fail;
- shear fail.

The sample values are public synthetic/manual validation values. They are not
real SCAD or LIRA files and are not a substitute for external engineering
validation.

Draft acceptance tolerances:

- bending delta percent <= 1.0;
- shear delta percent <= 1.0;
- Mcrc delta percent <= 1.0;
- crack width delta <= 0.005 mm;
- deflection delta <= 0.05 mm.

The sample is intended to verify the reporting pipeline from program values to
external values, deltas, acceptance status, and summary status.

## K33 Real-Data Intake Gate

K33 adds strict mode for engineer-filled CSV files. It does not add real SCAD,
LIRA, Excel, or private manual calculation files. Real external values must be
entered by an engineer in an anonymized CSV.

Strict mode checks:

- required columns are present;
- external values are filled;
- numeric fields parse correctly;
- deltas are provided or computed;
- deltas stay within draft tolerances;
- `acceptance_status` is consistent with missing values, numeric parsing, and
  tolerance results.

Strict status logic:

- `pass` when all cases are accepted, all external values are filled, and draft
  tolerances pass;
- `review_required` when values are missing, review rows are present, or
  acceptance status is inconsistent without a tolerance failure;
- `fail` when tolerances fail or explicit failed cases are present.

Use the checklist before committing anonymized external validation rows:

`docs/validation/external_validation_engineer_checklist.md`

The blank engineer input template is:

`docs/validation/templates/external_validation_engineer_input_template.csv`
