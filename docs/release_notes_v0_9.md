# v0.9 Engineering Release Notes

K90 adds release notes for the v0.9 engineering review package.

Run:

```bash
python -m sp63_core release-notes \
  --output-dir reports/release_notes_v0_9_smoke \
  --version 0.9.0-rc1 \
  --json
```

The v0.9 preparation sprint adds:

- K83 material verification closure workflow;
- K84 clean deterministic demo workflow;
- K85 engineering handoff package;
- K86 launcher scripts package;
- K87 external validation evidence package;
- K88 v0.9 final audit;
- K89 agent sprint guard;
- K90 release notes package.

This release note package does not publish a release, certify designs, approve
project use, change formulas, change materials, implement UI, or make ML a
calculator.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
