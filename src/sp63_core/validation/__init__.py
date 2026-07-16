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
from sp63_core.validation.external_report import (
    EXTERNAL_PROVENANCE_COLUMNS,
    EXTERNAL_VALIDATION_COLUMNS,
    EXTERNAL_VALUES_REQUIRED_WARNING,
    ExternalValidationSummary,
    ExternalValidationTolerance,
    build_external_validation_summary,
    load_external_validation_csv,
    validate_external_validation_rows,
)
from sp63_core.validation.golden import (
    GoldenCaseResult,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_deflection_golden_cases,
    run_design_golden_cases,
    run_shear_golden_cases,
    run_step3_bending_benchmark_cases,
)
from sp63_core.validation.manual_cases import (
    ManualVerificationCase,
    ManualVerificationResult,
    run_manual_verification_cases,
)
from sp63_core.validation.scad_lira_template import build_scad_lira_comparison_template

__all__ = [
    "DatasetValidationResult",
    "ExternalComparisonRow",
    "ExternalValidationSummary",
    "ExternalValidationTolerance",
    "EXTERNAL_PROVENANCE_COLUMNS",
    "EXTERNAL_VALIDATION_COLUMNS",
    "EXTERNAL_VALUES_REQUIRED_WARNING",
    "GoldenCaseResult",
    "ManualVerificationCase",
    "ManualVerificationResult",
    "build_external_comparison_rows",
    "build_external_validation_summary",
    "build_scad_lira_comparison_template",
    "compute_external_deltas",
    "evaluate_acceptance_gates",
    "external_row_has_completed_source",
    "export_acceptance_report_json",
    "export_external_comparison_csv",
    "export_external_comparison_with_deltas_csv",
    "load_external_comparison_csv",
    "load_external_validation_csv",
    "run_bending_golden_cases",
    "run_crack_formation_golden_cases",
    "run_crack_width_golden_cases",
    "run_deflection_golden_cases",
    "run_design_golden_cases",
    "run_manual_verification_cases",
    "run_shear_golden_cases",
    "run_step3_bending_benchmark_cases",
    "validate_dataset_cases",
    "validate_external_validation_rows",
]
