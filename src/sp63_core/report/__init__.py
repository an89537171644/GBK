"""Calculation report helpers for the SP 63 MVP."""

from sp63_core.report.archive_validation import (
    ReportArchiveValidationResult,
    validate_batch_report_archive,
    validate_report_bundle,
)
from sp63_core.report.batch_report import BatchDesignReportResult, build_batch_design_reports
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
from sp63_core.report.manifest import (
    ReportArtifactManifest,
    build_report_manifest,
    compute_file_sha256,
    report_manifest_as_dict,
    write_report_manifest_json,
)
from sp63_core.report.protocol import CalculationProtocol, build_calculation_protocol

__all__ = [
    "ALLOWED_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "BatchDesignReportResult",
    "CalculationProtocol",
    "DesignCalculationReport",
    "OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS",
    "ReportArchiveValidationResult",
    "ReportArtifactManifest",
    "build_calculation_protocol",
    "build_batch_design_reports",
    "build_report_manifest",
    "build_rectangular_design_report",
    "compute_file_sha256",
    "load_rectangular_design_input_from_json",
    "report_manifest_as_dict",
    "render_rectangular_design_report_html",
    "render_rectangular_design_report_markdown",
    "rectangular_design_input_from_mapping",
    "validate_batch_report_archive",
    "validate_report_bundle",
    "write_report_manifest_json",
]
