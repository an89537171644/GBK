# External validation engineer checklist

requires_engineer_review = true

## Purpose

This checklist defines how engineer-filled external validation CSV files should
be prepared before running the strict acceptance gate.

K33 does not add real SCAD, LIRA, Excel, or private calculation files. It only
defines the intake checks for anonymized numeric comparison data.

## Allowed Sources

External values may come from:

- independent manual calculations;
- engineer-maintained Excel templates;
- SCAD result summaries;
- LIRA result summaries.

Only anonymized numeric comparison rows should be committed. Closed model files,
private reports, personal data, grant documents, scans, and full normative text
must not be committed.

## Required Engineer Inputs

For every validation case, the engineer should fill:

- `source_type`;
- geometry and material identifiers;
- program output values;
- external output values;
- external strength, serviceability, and overall statuses;
- delta values, or leave them for the strict report to compute where possible;
- `acceptance_status`;
- `engineer_comment` for every review or failed case;
- `requires_engineer_review = true`.

## Strict Gate

Run:

```bash
python -m sp63_core external-validation --csv path/to/engineer_filled.csv --strict --json
```

Strict mode checks:

- all required columns are present;
- external values are filled;
- numeric fields parse correctly;
- deltas are available or computed;
- deltas stay within draft tolerances;
- `acceptance_status` is consistent with the strict checks.

## Draft Tolerances

- bending delta percent <= 1.0;
- shear delta percent <= 1.0;
- Mcrc delta percent <= 1.0;
- crack width delta <= 0.005 mm;
- deflection delta <= 0.05 mm.

## Safety Notes

External validation does not make ML a calculator. ML and neural surrogate
outputs remain advisory-only, and deterministic SP63 checks remain mandatory.
