# Release Bundle ZIP

K95 builds a review-only release bundle ZIP for v0.9 engineering review.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Command

```bash
python -m sp63_core release-bundle \
  --output-dir reports/release_bundle_smoke \
  --version 0.9.0-rc1 \
  --json
```

## Includes

- user manual docs;
- clean demo input;
- project template;
- launcher scripts;
- release notes;
- known limitations;
- acceptance checklist;
- release bundle manifest and report.

## Excludes

- generated reports and smoke artifacts;
- full SP 63 text;
- personal, grant, private, SCAD, or LIRA files;
- exe/binary artifacts;
- UI frameworks or web servers.

The bundle does not publish a GitHub release and does not certify designs.
