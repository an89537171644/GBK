# K85 Engineering Handoff Package

K85 adds a portable engineering handoff package for v0.9 review.

Run:

```bash
python -m sp63_core engineering-handoff-package --output-dir reports/engineering_handoff_package_smoke --json
```

The package includes:

- editable deterministic input JSON;
- clean deterministic demo input;
- external validation engineer-input CSV template;
- material verification engineer-input CSV template;
- copied quickstart and acceptance checklist;
- static input form preview;
- recommended run commands;
- SHA256 manifest.

The package is a scaffold only. It does not run calculations, certify designs,
update material values, include full SP 63 text, include private documents, add
UI dependencies, or make ML project-ready.

Safety flags:

- `requires_engineer_review = true`
- `ml_is_advisory_only = true`
- `deterministic_checks_required = true`
- `ml_ready_for_project_use = false`

Engineers must fill evidence CSV files manually, run deterministic SP63 checks,
review generated reports, and complete external/material validation before any
project use is considered.
