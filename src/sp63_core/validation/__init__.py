"""Validation helpers for the SP 63 draft MVP."""

from sp63_core.validation.dataset_checks import (
    DatasetValidationResult,
    validate_dataset_cases,
)
from sp63_core.validation.golden import (
    GoldenCaseResult,
    run_bending_golden_cases,
    run_design_golden_cases,
    run_shear_golden_cases,
)
from sp63_core.validation.scad_lira_template import build_scad_lira_comparison_template

__all__ = [
    "DatasetValidationResult",
    "GoldenCaseResult",
    "build_scad_lira_comparison_template",
    "run_bending_golden_cases",
    "run_design_golden_cases",
    "run_shear_golden_cases",
    "validate_dataset_cases",
]
