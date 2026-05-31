# Batch design reports

requires_engineer_review = true

## Purpose

K38 adds batch generation for draft rectangular beam design reports. It runs the
existing input-driven report workflow for several public JSON inputs and writes
one report bundle per case plus shared index files.

This is a reporting layer only. It does not change calculation formulas,
material values, reinforcement selection algorithms, or ML behavior.

## Input

Input files use the same rectangular design report JSON schema documented in
`docs/reports/design_report_input_schema.md`.

The CLI accepts either a directory:

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch
```

or repeated JSON files:

```bash
python -m sp63_core design-report-batch --input-json case_1.json --input-json case_2.json --output-dir reports/batch
```

JSON summary mode is available:

```bash
python -m sp63_core design-report-batch --input-dir docs/reports/examples/batch --output-dir reports/batch --json
```

## Output

The output directory contains:

- `index.md`;
- `index.json`;
- one subdirectory per input, such as `case_001`, `case_002`, `case_003`.

Each valid case directory contains:

- `report.md`;
- `report.json`;
- `report.html`;
- copied `input.json`;
- `manifest.json`.

The batch root directory also contains `manifest.json`.

## Index

The Markdown and JSON indexes include:

- `case_id`;
- `input_file`;
- `strength_status`;
- `serviceability_status`;
- `overall_status`;
- `warnings_count`;
- `report_path`;
- `manifest_path`;
- `input_sha256`;
- `report_json_sha256`;
- `report_markdown_sha256`;
- `report_html_sha256`;
- `requires_engineer_review`.

Invalid input JSON files are reported as `input_error` without stopping the
remaining batch cases.

## Archive Validation

K40 adds a validation command for completed batch archives:

```bash
python -m sp63_core report-archive-validate --path reports/batch --batch --json
```

The command checks root and case manifests, required case files, SHA256 values,
and consistency between `index.json` and case-level manifests.

## Limitations

- rectangular beam draft-MVP only;
- report output is not a certified design conclusion;
- all reports require engineer review;
- material verification remains a separate gate;
- external validation remains a separate gate;
- full SP 63 text is not stored in the repository;
- ML remains advisory-only;
- deterministic SP63 checks remain mandatory.
