# v0.9 Review Closure

K107 adds a manual review closure and release-candidate stabilization report.

The command aggregates the current v0.9 evidence stack:

- protected-files-check;
- docs-audit;
- clean-demo-workflow;
- clean-demo-verify;
- release-acceptance-checklist;
- v09-final-audit;
- v09-freeze-report;
- v09-review-build;
- next-release-roadmap.

Run:

```bash
python -m sp63_core v09-review-closure \
  --output-dir reports/v09_review_closure_smoke \
  --version 0.9.0-rc1 \
  --json
```

It writes:

- `v09_review_closure.json`;
- `v09_review_closure.md`;
- `README_V09_REVIEW_CLOSURE.md`.

K107 is review evidence only. It does not certify calculations, approve project
use, close material engineer verification, close real external validation, or
close manual signoff.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`
- `ready_for_project_use = false`
