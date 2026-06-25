# v1.0 Gap And Risk Report

K97 documents what remains before any v1.0 readiness claim.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false
ready_for_v10 = false

## Command

```bash
python -m sp63_core v10-gap-report --output-dir reports/v10_gap_report_smoke --json
```

## K106 next release roadmap

K106 adds `next-release-roadmap` to turn the v1.0 gaps into a planning roadmap
for v0.9 internal review, v0.9 user trial, v1.0 engineering release,
GUI/launcher, material verification, external validation, ML advisory maturity,
and installer/packaging milestones.

## Open Gaps

- material verification;
- real external validation;
- safe GUI/launcher workflow;
- packaging/installer process;
- ML production governance;
- documentation completion.

The report is planning evidence only and does not certify designs.
