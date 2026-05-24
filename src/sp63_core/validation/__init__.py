"""Validation helpers for the SP 63 draft MVP."""

from sp63_core.validation.dataset_checks import (
    DatasetValidationResult,
    validate_dataset_cases,
)
from sp63_core.validation.external import (
    ExternalComparisonRow,
    build_external_comparison_rows,
    compute_external_deltas,
    evaluate_acceptance_gates,
    export_acceptance_report_json,
    export_external_comparison_csv,
    export_external_comparison_with_deltas_csv,
    external_row_has_completed_source,
    load_external_comparison_csv,
)
from sp63_core.validation.golden import (
    GoldenCaseResult,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_deflection_golden_cases,
    run_design_golden_cases,
    run_shear_golden_cases,
)
from sp63_core.validation.scad_lira_template import build_scad_lira_comparison_template

__all__ = [
    "DatasetValidationResult",
    "ExternalComparisonRow",
    "GoldenCaseResult",
    "build_external_comparison_rows",
    "build_scad_lira_comparison_template",
    "compute_external_deltas",
    "evaluate_acceptance_gates",
    "external_row_has_completed_source",
    "export_acceptance_report_json",
    "export_external_comparison_csv",
    "export_external_comparison_with_deltas_csv",
    "load_external_comparison_csv",
    "run_bending_golden_cases",
    "run_crack_formation_golden_cases",
    "run_crack_width_golden_cases",
    "run_deflection_golden_cases",
    "run_design_golden_cases",
    "run_shear_golden_cases",
    "validate_dataset_cases",
]
