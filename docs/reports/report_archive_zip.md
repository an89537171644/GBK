# Report archive ZIP export

requires_engineer_review = true

## Purpose

K41 adds ZIP export for report archive directories created by `design-report
--bundle-output` and `design-report-batch`. The ZIP file is intended for safe
handoff to engineering review or long-term project archiving.

This is a packaging and integrity layer only. It does not certify a calculation
result and does not change formulas, material values, reinforcement selection,
ML behavior, or validation gates.

## Single Bundle ZIP

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
```

The ZIP includes the archive files with relative paths:

- `manifest.json`;
- `report.md`;
- `report.json`;
- `report.html`;
- `input.json`.

## Batch Archive ZIP

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

The ZIP includes:

- root `manifest.json`;
- `index.md`;
- `index.json`;
- case folders with `manifest.json`, `report.md`, `report.json`,
  `report.html`, and `input.json`.

If `--batch` is omitted and `index.json` exists, the archive is still treated
as a batch archive by the pre-export validation step.

## ZIP SHA256

`zip_sha256` is the SHA256 checksum of the created ZIP file. It can be stored
outside the package to detect whether the ZIP itself changed after export.

## ZIP Validation

The export command validates the source archive before creating the ZIP and
validates the ZIP after creation. ZIP validation checks that:

- the ZIP opens successfully;
- entries are relative paths;
- entries do not contain `..`;
- single bundles contain the expected report files;
- batch archives contain root index/manifest files and case folders;
- `requires_engineer_review = true` is preserved in the result.

## Security

The ZIP validator rejects path traversal entries such as `../escape.txt` and
absolute paths. K41 does not extract ZIP files into arbitrary directories.

## Limitations

- ZIP export does not certify the design result;
- engineer review remains required;
- material verification remains a separate gate;
- external validation remains a separate gate;
- full SP 63 text is not stored in the repository;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory.
