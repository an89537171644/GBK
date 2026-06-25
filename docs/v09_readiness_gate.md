# v0.9 Readiness Gate

K82 adds a final aggregated readiness gate for the v0.9 engineering review
package:

```bash
python -m sp63_core v09-readiness --output-dir reports/v09_readiness_smoke --json
python -m sp63_core v09-readiness --output-dir reports/v09_readiness_smoke --markdown
```

The command writes:

- `v09_readiness_report.json`
- `v09_readiness_report.md`
- nested release manifest, user acceptance smoke, and release candidate reports

The gate aggregates these review checks:

- `protected-files-check`
- `docs-audit`
- `release-manifest`
- `user-acceptance-smoke`
- `release-candidate-report`

Status logic:

- `fail` if any nested gate fails;
- `review_required` if any nested gate requires review;
- `pass` only if every nested gate passes.

`review_required` is an expected outcome while engineer material verification,
external validation, and release approval gates remain open. The readiness gate
is evidence for review only. It does not publish a release, certify designs,
change formulas, change material values, update reinforcement selection, or
make ML project-ready.

Safety flags remain fixed:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`

