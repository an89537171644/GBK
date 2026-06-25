# Freeze Remediation Plan

K99 adds a review-only remediation plan for the expected `review_required`
status of `v09-freeze-report` and `v10-gap-report`.

The plan does not force review gates to pass. It records open material,
external validation, ML advisory, project-use, GUI/installer, Windows
clean-machine, and engineer-review gaps so they can be handled explicitly.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
- `project_use_allowed = false`

Example:

```bash
python -m sp63_core freeze-remediation-plan --output-dir reports/freeze_remediation_plan_smoke --json
```

Generated smoke folders are local review artifacts and must not be committed.
