"""Calculation report helpers for the SP 63 MVP."""

from sp63_core.report.design_report import (
    DesignCalculationReport,
    build_rectangular_design_report,
    render_rectangular_design_report_html,
    render_rectangular_design_report_markdown,
)
from sp63_core.report.design_report_input import (
    ALLOWED_RECTANGULAR_DESIGN_INPUT_FIELDS,
    OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS,
    REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS,
    load_rectangular_design_input_from_json,
    rectangular_design_input_from_mapping,
)
from sp63_core.report.protocol import CalculationProtocol, build_calculation_protocol

__all__ = [
    "ALLOWED_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "CalculationProtocol",
    "DesignCalculationReport",
    "OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "build_calculation_protocol",
    "build_rectangular_design_report",
    "load_rectangular_design_input_from_json",
    "render_rectangular_design_report_html",
    "render_rectangular_design_report_markdown",
    "rectangular_design_input_from_mapping",
]
