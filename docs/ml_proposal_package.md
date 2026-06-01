# ML Proposal Package — Advisory Only

requires_engineer_review = true

## Purpose

K50 packages one advisory ML status proposal together with deterministic SP63
verification and the K49 neural safety audit.

The workflow is:

```text
input.json -> neural advisory prediction -> neural safety audit -> deterministic SP63 verification -> ML proposal package -> engineer review
```

The package is not a design calculation. ML and neural outputs remain
advisory-only. Deterministic SP63 results are the authority.

## Commands

JSONL dataset:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

CSV dataset:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.csv --format csv --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

Review-only deterministic-derived feature mode:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --feature-mode deterministic_derived --input-json docs/reports/examples/rectangular_design_input_example.json --json
```

Markdown output:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown
```

Markdown file:

```bash
python -m sp63_core ml-proposal-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --markdown --output reports/ml_proposal_package.md
```

## Proposal Statuses

`proposal_status = accepted` is possible only as an advisory signal. It requires
deterministic verification to pass, prediction and deterministic target status
to match, safety audit not to fail, no errors, and mandatory safety flags to be
present.

`proposal_status = review_required` is used when deterministic results pass but
the ML evidence is not sufficient for trust. Typical review reasons are small
datasets, missing material verification context, missing external validation
context, low confidence, or other safety warnings.

`proposal_status = rejected` is used when deterministic verification fails or is
unavailable, deterministic overall status is `fail` or `review_or_fail`, the ML
prediction differs from deterministic status, target data is unavailable, or the
K49 safety audit fails.

## Output

The JSON and Markdown reports include:

- source dataset and input JSON path;
- target and feature mode;
- predicted status, prediction confidence, and class probabilities;
- deterministic strength, serviceability, and overall statuses;
- `prediction_matches_deterministic`;
- `advisory_signal_usable`;
- `safety_audit_status`;
- proposal accept/reject/review flags;
- rejection or review reasons;
- warnings and errors.

## Required Safety Notes

Every package result includes these principles:

```text
ML proposal is advisory-only
deterministic SP63 verification is mandatory
accepted result still requires engineer review
ML output cannot be used as a design decision
```

Material verification and external validation remain separate engineer gates.

## Limitations

- K50 does not change deterministic SP63 formulas.
- K50 does not change material values.
- K50 does not change reinforcement selection.
- K50 does not make ML a calculator.
- K50 does not add a new neural-network dependency.
- K50 reuses the K48/K49 advisory prediction and safety audit path.
- The generated package is not certification evidence.
- Engineer review remains mandatory before any project use.

## K51 Review ZIP Package

K51 adds `ml-proposal-review-package` as a handoff layer around this proposal
package:

```bash
python -m sp63_core ml-proposal-review-package --dataset reports/batch_dataset.jsonl --input-json docs/reports/examples/rectangular_design_input_example.json --output-dir reports/ml_proposal_review --json
```

It stores the original input, deterministic report, neural safety audit, this
ML proposal package, a review README, manifest checksums, and optional ZIP
archive. The ZIP/manifest package does not certify the design and does not make
ML a calculator.
