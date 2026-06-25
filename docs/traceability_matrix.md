# Traceability Matrix

K96 maps main v0.9 review features to CLI commands, documentation, tests, and
safety warnings.

requires_engineer_review = true
ml_is_advisory_only = true
deterministic_checks_required = true
ml_ready_for_project_use = false

## Command

```bash
python -m sp63_core traceability-matrix --json
python -m sp63_core traceability-matrix --markdown
python -m sp63_core traceability-matrix --output-dir reports/traceability_matrix_smoke --json
```

The matrix is navigation and review evidence only. It does not approve project
use.
