# K88 v0.9 Final Audit

K88 adds an aggregated v0.9 final audit report.

Run:

```bash
python -m sp63_core v09-final-audit --output-dir reports/v09_final_audit_smoke --json
```

The audit summarizes:

- protected files guard;
- docs audit;
- v0.9 readiness gate;
- clean deterministic demo workflow;
- engineering handoff package;
- launcher scripts package;
- material verification closure sample;
- external validation evidence package sample.

The audit may return `review_required` while manual engineer review gates remain
open. This is expected and does not block report generation.

K88 does not publish a release, certify calculations, approve project use,
change formulas, change material values, implement UI, or make ML a calculator.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`

K107 uses the final audit as one input to the review closure report:

```bash
python -m sp63_core v09-review-closure --output-dir reports/v09_review_closure_smoke --version 0.9.0-rc1 --json
```

The closure report may allow manual v0.9 review handoff evidence, but it keeps
`ready_for_project_use = false`.

K108 includes the final audit in the v0.9 release candidate package:

```bash
python -m sp63_core v09-release-candidate-package --output-dir reports/v09_release_candidate_package_smoke --version 0.9.0-rc1 --json
```
