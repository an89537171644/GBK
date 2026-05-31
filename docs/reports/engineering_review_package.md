# Engineering review package README

requires_engineer_review = true

## Purpose

K42 adds `README_REVIEW.md` to generated single report bundles and batch report
archives. The file is a human-readable guide for engineers receiving a ZIP
package or archive folder.

The README explains what is inside the archive, how to validate the archive and
ZIP, how to reproduce a report from `input.json`, where key files are located,
and which final statuses require attention.

## Single Bundle

```bash
python -m sp63_core design-report --input-json docs/reports/examples/rectangular_design_input_example.json --bundle-output reports/smoke_case
```

The generated folder contains:

- `README_REVIEW.md`;
- `manifest.json`;
- `input.json`;
- `report.md`;
- `report.json`;
- `report.html`.

`README_REVIEW.md` is included in `manifest.json` checksums and in ZIP export.

## Batch Archive

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch_smoke
```

The batch root contains:

- `README_REVIEW.md`;
- `manifest.json`;
- `index.md`;
- `index.json`;
- `case_###` folders with case reports and manifests.

K42 creates one root README for the batch archive. Case-level README files are
not required in this step.

## Validation

```bash
python -m sp63_core report-archive-validate --path reports/smoke_case --json
python -m sp63_core report-archive-validate --path reports/batch_smoke --batch --json
python -m sp63_core report-archive-zip --path reports/smoke_case --output reports/smoke_case.zip --json
python -m sp63_core report-archive-zip --path reports/batch_smoke --output reports/batch_smoke.zip --batch --json
```

Archive validation treats a missing `README_REVIEW.md` as an incomplete package.
ZIP validation also expects the README in single and batch root entries.

## Dataset Export

K43 can export ML-ready rows from a validated report archive:

```bash
python -m sp63_core report-dataset-export --path reports/smoke_case --output reports/smoke_dataset.jsonl --json
python -m sp63_core report-dataset-export --path reports/batch_smoke --batch --output reports/batch_dataset.jsonl --json
```

The export reads existing `report.json`, `input.json`, and `manifest.json`
files. It does not recalculate the design and does not train an ML model.

## Limitations

- `README_REVIEW.md` is documentation and does not certify the calculation;
- the calculation remains a draft-MVP artifact;
- engineer review remains required;
- material verification remains a separate gate;
- external validation remains a separate workflow;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory;
- full SP 63 text is not included.
