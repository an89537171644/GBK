# Release Acceptance Checklist

K103 adds a machine-readable acceptance checklist for v0.9 review.

The checklist includes machine-checkable evidence commands and manual signoff
items. It remains `review_required` while manual material, external validation,
known limitations, and engineer signoff gates are open.

The checklist does not approve project use.

```bash
python -m sp63_core release-acceptance-checklist --output-dir reports/release_acceptance_checklist_smoke --json
```

K107 includes the checklist in the v0.9 review closure report:

```bash
python -m sp63_core v09-review-closure --output-dir reports/v09_review_closure_smoke --version 0.9.0-rc1 --json
```

Manual signoff rows remain open and are not auto-closed by the closure report.

K108 also includes this checklist in the final release candidate package:

```bash
python -m sp63_core v09-release-candidate-package --output-dir reports/v09_release_candidate_package_smoke --version 0.9.0-rc1 --json
```
