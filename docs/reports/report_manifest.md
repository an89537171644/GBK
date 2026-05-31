# Report bundle manifest

requires_engineer_review = true

## Purpose

K39 adds `manifest.json` files to single and batch design report bundles. The
manifest records reproducibility metadata for engineering archiving and later
review.

This is a traceability layer only. It does not make the calculation certified
and does not change formulas, material values, reinforcement selection, or ML
behavior.

## Manifest Structure

Each manifest includes:

- `manifest_version`;
- `report_type`;
- `generated_at_utc`;
- `command`;
- `input_files`;
- `output_files`;
- `status`;
- `strength_status`;
- `serviceability_status`;
- `overall_status`;
- `warnings_count`;
- `metadata`;
- `requires_engineer_review = true`.

File records include:

- `path`;
- `sha256`;
- `size_bytes`.

## SHA256

SHA256 is a cryptographic checksum used here to detect whether an input or
report artifact changed after generation. To verify reproducibility, compare
the checksum stored in `manifest.json` with the checksum recomputed for the
file in the archived bundle.

## Single Bundle

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The output directory contains:

- `report.md`;
- `report.json`;
- `report.html`;
- `input.json`;
- `manifest.json`.

## Batch Bundle

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
```

The batch output contains:

- root `manifest.json`;
- `index.md`;
- `index.json`;
- case directories with their own `manifest.json`.

The batch `index.json` also stores each case manifest path and checksums for
the copied input and report outputs.

## Archive Validation

K40 adds a validation command for archives that already contain K39 manifests:

```bash
python -m sp63_core report-archive-validate --path reports/smoke_case --json
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
```

The command recomputes SHA256 values, reports missing files, and checks batch
`index.json` consistency with case manifests. Details are documented in
`docs/reports/report_archive_validation.md`.

K41 adds ZIP export for validated archives:

```bash
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
```

The ZIP result includes `zip_sha256` for handoff integrity checks.

## Limitations

- manifest metadata does not certify the design result;
- engineer review remains required;
- material verification remains a separate gate;
- external validation remains a separate gate;
- full SP 63 text is not stored in the repository;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory.
