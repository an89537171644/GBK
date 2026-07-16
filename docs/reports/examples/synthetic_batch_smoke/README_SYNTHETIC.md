# Synthetic report input cases

These files are anonymized synthetic design-report input cases generated for
report-derived dataset and ML smoke experiments.

- generator: `synthetic_report_inputs`
- case_count: `10`
- seed: `42`
- synthetic_data_only: `true`
- completeness_status: `incomplete`
- evidence_status: `needs_engineer_review`
- project_use_status: `prohibited`
- project_use: `false`
- requires_engineer_review: `true`
- ml_is_advisory_only: `true`
- deterministic_checks_required: `true`
- serviceability: Serviceability fields are included with mixed crack, crack-width, and deflection flags.

Synthetic data does not replace material verification, manual checks, or
external validation with engineer-filled SCAD/LIRA/Excel/manual values.
Large generated report outputs should stay local and should not be committed.
