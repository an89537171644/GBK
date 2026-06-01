# ML Proposal Engineering Review Package

requires_engineer_review = true

## Purpose

K51 adds an engineer-facing package for one advisory ML proposal.

The workflow is:

```text
input.json -> deterministic SP63 report -> neural safety audit -> ML proposal package -> manifest -> ZIP -> engineer review
```

The package is not a design calculation. It does not certify the result. ML
proposal output remains advisory-only, and deterministic SP63 verification is
mandatory.

## Commands

JSONL dataset:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review --json
```

CSV dataset:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_csv --json
```

Review-only deterministic-derived feature mode:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_derived --json
```

Directory-only mode:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review_nozip --no-zip --json
```

## Package Contents

```text
input.json
deterministic_report.md
deterministic_report.json
deterministic_report.html
neural_safety_audit.md
neural_safety_audit.json
ml_proposal_package.md
ml_proposal_package.json
README_REVIEW.md
manifest.json
```

When ZIP export is enabled, the command also creates `<output-dir>.zip`.

## Manifest

The manifest records:

- `report_type = "ml_proposal_engineering_review_package"`;
- source dataset and input JSON path;
- target and feature mode;
- proposal status;
- deterministic strength, serviceability, and overall statuses;
- prediction match flag;
- advisory signal usability;
- safety audit status;
- engineer review and advisory-only flags;
- SHA256 checksums for package payload files.

`manifest.json` itself is included in the package and ZIP. Its self-checksum is
not embedded in the manifest because a manifest cannot contain a stable checksum
of itself.

## README_REVIEW.md

The review README explains:

- package purpose;
- package contents;
- final proposal and deterministic statuses;
- how to check manifest and ZIP SHA256;
- how to rerun deterministic report from `input.json`;
- how to rerun `ml-proposal-package`;
- limitations and review gates.

## Safety Notes

- ML is advisory-only.
- ML proposal is not a project design decision.
- Deterministic SP63 verification is mandatory.
- Engineer review is mandatory.
- Material verification remains separate.
- External validation remains separate.
- Metrics and predictions are not production evidence.
- ZIP and manifest packaging do not certify the design.

## Limitations

- K51 does not change deterministic SP63 formulas.
- K51 does not change material values.
- K51 does not change reinforcement selection algorithms.
- K51 does not make ML a calculator.
- K51 does not add PyTorch, TensorFlow, or Keras.
- K51 does not add UI or Streamlit.
- K51 does not include full SP 63 text.
- K51 does not include personal, grant, private, or closed SCAD/LIRA files.

## K60 Engineering Bundle

The K60 `engineering-ml-readiness` command can reference a proposal package JSON
inside this review folder. The evidence is included in the readiness matrix as
`ml_proposal_package`.

The proposal package remains advisory-only and does not approve ML for project
use.
