# Codex automation plan

## Purpose

This document defines how Codex should work in the GBK repository.

The goal is to allow Codex to work almost automatically while keeping
engineering control over SP 63 formulas and deterministic calculation safety.

## Workflow

1. Human creates or approves a GitHub Issue.
2. Issue receives label:
   codex-ready
3. Codex reads the issue.
4. Codex creates a feature branch.
5. Codex implements only the requested task.
6. Codex runs required tests.
7. Codex commits changes.
8. Codex pushes the branch.
9. Codex opens a Pull Request.
10. Human reviews the PR.
11. Human merges PR only if accepted.

## Forbidden

- Direct push to main.
- Auto-merge.
- Multiple engineering steps in one PR.
- Changing formulas without explicit task approval.
- Treating ML as a calculator.
- Committing private documents or personal data.
- Committing full normative text.
- Removing requires_engineer_review from engineering modules without explicit
  approval.

## Required checks

Always:

python -m pytest
ruff check .

For validation changes:

python -m sp63_core validate --golden
python -m sp63_core validate --generate-dataset-limit 20 --json

For dataset changes:

python -m sp63_core generate-dataset --limit 20 --split --group-split --output-dir data/generated --prefix smoke_dataset --report reports/interim/smoke_dataset_report.json

For ML changes:

python -m sp63_core train-baseline --generate-dataset-limit 50 --model-output models/smoke_baseline.pkl --metrics-output reports/interim/smoke_baseline_metrics.json

## Current task queue

K14 - normal crack formation Mcrc
K15 - normal crack width acrc
K16 - curvature and deflection draft MVP
K17 - serviceability dataset extension
K18 - ML serviceability baseline
K19 - model card and grant report package
K20 - UI prototype, only after engineering checks

## Issue labels

- codex-ready - task is ready for Codex
- codex-in-progress - Codex is working
- engineer-review - requires engineering review
- formula-change - formulas may be changed only if issue explicitly allows it
- ml-sandbox - ML-related task
- serviceability - second limit-state task
- validation - validation task
- dataset - dataset task
- ui - UI task

## Automation prompt

Codex automation should use this prompt:

"Pick exactly one open GitHub Issue with label codex-ready and without label
codex-in-progress. Read AGENTS.md and docs/codex_automation_plan.md. Create a
feature branch. Implement only that issue. Run required tests. Commit changes.
Push the branch. Open a Pull Request. Do not merge. Do not push directly to
main. Stop after opening PR."

## Manual human responsibilities

Human must:

- approve or reject PR;
- verify engineering formulas;
- fill SCAD/LIRA comparison values;
- approve external validation;
- decide when ML can be shown as demonstration;
- keep main branch protected.
