# Report archive validation

requires_engineer_review = true

## Purpose

K40 adds an integrity check for report archives created by:

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
```

K39 added `manifest.json` files and SHA256 checksums. K40 verifies that the
archived files are still present, the stored checksums still match, and batch
`index.json` remains consistent with case-level manifests.

## Single Bundle Check

```bash
python -m sp63_core report-archive-validate --path reports/smoke_case --json
```

The command checks:

- `manifest.json` exists;
- `README_REVIEW.md` exists;
- `report.md`, `report.json`, `report.html`, and `input.json` exist;
- manifest `input_files` and `output_files` exist;
- SHA256 values match the files on disk;
- `requires_engineer_review = true`.

## Batch Archive Check

```bash
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
```

The command checks:

- root `manifest.json`, `README_REVIEW.md`, `index.md`, and `index.json` exist;
- every indexed case folder exists inside the archive directory;
- every case folder has `manifest.json`, `report.md`, `report.json`,
  `report.html`, and `input.json`;
- root and case manifest checksums match;
- `index.json` case checksum fields match current files;
- indexed case manifests do not escape the archive folder.

If `--batch` is omitted and `index.json` exists, the CLI treats the path as a
batch archive automatically.

## Status

The JSON result includes:

- `status`;
- `archive_path`;
- `manifest_count`;
- `checked_file_count`;
- `missing_file_count`;
- `checksum_mismatch_count`;
- `index_consistency_status`;
- `warnings`;
- `errors`;
- `requires_engineer_review`.

`status = pass` means no missing files, checksum mismatches, or index
consistency errors were found. `status = fail` means at least one archive
integrity problem was found.

## Checksum Mismatch

A checksum mismatch means that a file listed in a manifest or batch index was
changed after the manifest was created. The archive should be regenerated or
reviewed by an engineer before use.

## Missing Files

Missing files mean the archive is incomplete. The archive should not be used as
a reproducible engineering evidence bundle until the missing files are restored
or the report is regenerated.

## ZIP Export

K41 adds ZIP packaging for archives that pass this validation layer:

```bash
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

The ZIP command validates the source archive before packaging and validates the
ZIP after creation. K42 requires `README_REVIEW.md` in single bundles and batch
roots so the ZIP package carries human-readable review guidance. Details are documented in
`docs/reports/report_archive_zip.md`.

## Limitations

- archive validation does not certify the design result;
- engineer review remains required;
- material verification remains a separate gate;
- external validation remains a separate gate;
- full SP 63 text is not stored in the repository;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory.
