# Neural advisory prediction with deterministic verification

requires_engineer_review = true

## Purpose

K48 adds a safe advisory prediction workflow for one rectangular design input.

The workflow is:

```text
input.json -> neural advisory prediction -> deterministic SP63 design report -> comparison -> engineer review
```

The neural prediction is not a calculation result. It is a research signal only.
The deterministic SP63 report remains authoritative.

## Commands

JSONL dataset:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

CSV dataset:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

Deterministic-derived feature smoke mode:

```bash
python -m sp63_core report-neural-predict --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

## Safety Flow

The command always builds a deterministic design report from `input.json` and
returns:

- `deterministic_strength_status`;
- `deterministic_serviceability_status`;
- `deterministic_overall_status`;
- `prediction_matches_deterministic`.

If the neural prediction differs from the deterministic status, the command
returns `review_required` with warning:

```text
neural advisory prediction differs from deterministic SP63 result
```

## Leakage Protection

K48 uses K45 leakage-safe feature selection. Status, direct check result,
utilization, and target columns are not used as input features.

`deterministic_derived` can include selected deterministic outputs, but it
returns this warning:

```text
deterministic-derived features may leak design decisions and must not be used for project ML decisions without review
```

## Required Warnings

Every result includes:

```text
neural advisory prediction is not a design checker
deterministic SP63 verification is mandatory
engineer review is required before any project use
metrics and predictions are not production evidence
```

Small datasets with fewer than 100 rows also include:

```text
dataset is too small for reliable advisory prediction
```

## Limitations

- ML remains advisory-only.
- Neural prediction is not a project decision.
- Deterministic SP63 checks are mandatory.
- K30 safety-wrapper philosophy remains mandatory for any ML proposal.
- Engineer review is required before any project use.
- K48 does not change calculation formulas, material values, or reinforcement
  selection algorithms.
- K48 does not add PyTorch, TensorFlow, Keras, UI, Streamlit, full SP 63 text,
  personal documents, grant documents, or closed SCAD/LIRA files.

## K49 Safety Audit

K49 adds `neural-safety-audit` as an engineer-facing report layer on top of this
K48 command. It does not train another model and does not replace the
deterministic report.

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

The audit records the prediction, deterministic statuses, match flag,
`advisory_signal_usable`, `audit_status`, warnings, and rejection reasons. A
prediction mismatch or deterministic fail/review status blocks advisory signal
use and requires engineer review.

## K50 Proposal Package

K50 adds `ml-proposal-package` as an engineer-facing package for one advisory ML
proposal:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

It includes this K48 prediction, K49 safety audit status, deterministic SP63
statuses, class probabilities, proposal status, rejection/review reasons, and
Markdown output. The proposal package is advisory-only and cannot be used as a
design decision.

## K51 Review Package

K51 creates an engineer review folder and ZIP around K48/K49/K50 outputs:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review --json
```

It includes the deterministic report, neural safety audit, ML proposal package,
README_REVIEW.md, manifest checksums, and optional ZIP archive. The package is
for review handoff only and is not certification evidence.
