# v0.9 Freeze Report

K98 builds the final v0.9 freeze report for engineering review.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false
project_use_allowed = false

## Command

```bash
python -m sp63_core v09-freeze-report \
  --output-dir reports/v09_freeze_report_smoke \
  --version 0.9.0-rc1 \
  --json
```

## Included Gates

- protected-files-check;
- docs-audit;
- user-manual-index;
- release-notes;
- release-manifest;
- release-bundle;
- clean-demo-verify;
- traceability-matrix;
- v10-gap-report;
- v09-final-audit.

The freeze report is review evidence only. It does not certify designs or approve
project use.

K107 consumes this report in the v0.9 review closure command:

```bash
python -m sp63_core v09-review-closure --output-dir reports/v09_review_closure_smoke --version 0.9.0-rc1 --json
```

The closure output remains review evidence only and does not close material,
external validation, or manual signoff gates.

K108 includes this freeze report in the final v0.9 release candidate package:

```bash
python -m sp63_core v09-release-candidate-package --output-dir reports/v09_release_candidate_package_smoke --version 0.9.0-rc1 --json
```
