# CI Safety Workflow

requires_engineer_review = true

## Purpose

K76 adds a dedicated GitHub Actions safety workflow for agent-generated
workflow/release PRs. It runs deterministic validation, manual verification,
external-validation smoke, protected-files guard, and release-candidate smoke
checks before a reviewer considers merge.

The workflow is a review aid only. It does not certify calculations, approve a
project, or replace deterministic SP63 checks and engineer review.

## Workflow

The workflow file is:

```text
.github/workflows/safety.yml
```

It runs on `push` and `pull_request` for Python 3.10 and 3.11.

The checkout uses:

```yaml
fetch-depth: 0
```

This is required so `protected-files-check` can compare the branch against
`origin/main` reliably in GitHub Actions.

## Commands

```bash
python -m pytest
ruff check .
python -m sp63_core validate --golden
python -m sp63_core manual-cases --json
python -m sp63_core external-validation --sample --json
python -m sp63_core protected-files-check --json
python -m sp63_core release-candidate-report --output-dir reports/release_candidate_ci_smoke --json
```

`release-candidate-report` may return `review_required` while engineer gates
remain open. That does not fail CI by itself.

`protected-files-check` returns a nonzero CLI exit only when protected files
changed. `review_required` remains a review signal and should be investigated
when it appears in CI.

## Safety

- Calculation formulas are not changed by this workflow.
- Material values are not changed by this workflow.
- ML remains advisory-only.
- `ml_ready_for_project_use` must remain false.
- Generated smoke reports are runner-local artifacts and must not be committed.
