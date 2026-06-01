# Neural advisory safety audit

requires_engineer_review = true

## Purpose

K49 adds an engineer-facing safety audit for K48 neural advisory predictions.

The workflow remains:

```text
input.json -> neural advisory prediction -> deterministic SP63 verification -> comparison -> safety audit -> engineer review
```

The audit is not a design calculation. It documents what the neural advisory
signal predicted, what the deterministic SP63 report returned, whether those
statuses matched, and why deterministic verification remains mandatory.

## Commands

JSONL dataset:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

CSV dataset:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

Markdown output:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

Markdown file:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown --output reports/neural_safety_audit.md
```

Review-only deterministic-derived feature mode:

```bash
python -m sp63_core neural-safety-audit --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

## Audit statuses

`audit_status = pass` is possible only when the advisory prediction matches the
deterministic target status, deterministic overall status is `pass`, there are
no errors, and the advisory-only safety flags are present.

`audit_status = review_required` is used for cases such as small datasets,
review-only deterministic-derived features, non-production metrics, or missing
material/external verification context.

`audit_status = fail` is used for prediction mismatch, deterministic `fail` or
`review_or_fail`, missing target data, K48 errors, or failure to complete
deterministic verification.

## Advisory signal

`advisory_signal_usable` can be true only when deterministic verification ran,
the prediction matched the deterministic target status, there are no errors,
ML remains advisory-only, and engineer review is still required.

Even when `advisory_signal_usable = true`, the result is not a project design
decision. It is only a review signal.

## Required warnings

Every audit result includes:

```text
neural advisory prediction is not a design checker
deterministic SP63 verification is mandatory
engineer review is required before any project use
metrics and predictions are not production evidence
```

Small report-derived datasets include:

```text
dataset is too small for reliable advisory prediction
```

The deterministic-derived mode includes:

```text
deterministic-derived features may leak design decisions and must not be used for project ML decisions without review
```

Prediction mismatch includes:

```text
neural advisory prediction differs from deterministic SP63 result
```

## Limitations

- K49 does not change deterministic SP63 formulas.
- K49 does not change material values.
- K49 does not change reinforcement selection.
- K49 does not make ML a calculator.
- Neural advisory output is not a project decision.
- K30 safety-wrapper philosophy remains mandatory for ML proposals.
- Material verification and external validation remain separate engineer gates.
- Metrics and predictions are not production evidence.
- Engineer review remains mandatory.

## K50 Proposal Package

K50 adds `ml-proposal-package` as the next review layer after this safety audit:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

The package reuses the K48 prediction and this K49 audit, then records
`proposal_status`, proposal accept/reject/review flags, rejection or review
reasons, warnings, class probabilities, and deterministic SP63 statuses.
Acceptance remains advisory-only and is not a project decision.
