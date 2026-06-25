# Release Acceptance Checklist

K103 adds a machine-readable acceptance checklist for v0.9 review.

The checklist includes machine-checkable evidence commands and manual signoff
items. It remains `review_required` while manual material, external validation,
known limitations, and engineer signoff gates are open.

The checklist does not approve project use.

```bash
python -m sp63_core release-acceptance-checklist --output-dir reports/release_acceptance_checklist_smoke --json
```
