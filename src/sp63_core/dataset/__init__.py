"""Dataset generation helpers for the SP 63 MVP."""

from sp63_core.dataset.diagnostic import (
    DIAGNOSTIC_DATASET_SOURCE,
    DiagnosticDatasetCase,
    DiagnosticDatasetSplit,
    diagnostic_dataset_warnings,
    diagnostic_group_leakage_count,
    diagnostic_status_counts,
    diagnostic_unique_group_count,
    generate_diagnostic_dataset_cases,
    split_diagnostic_dataset_by_group,
)
from sp63_core.dataset.from_reports import (
    REPORT_DATASET_SOURCE,
    SUPPORTED_REPORT_DATASET_FORMATS,
    ReportDatasetExportResult,
    export_dataset_from_report_archive,
    extract_dataset_row_from_report_json,
)
from sp63_core.dataset.generator import (
    DATASET_COLUMNS,
    DATASET_VERSION,
    DatasetCase,
    export_dataset_csv,
    generate_dataset_cases,
)
from sp63_core.dataset.quality_gate import (
    REQUIRED_REPORT_DATASET_COLUMNS,
    SUPPORTED_REPORT_QUALITY_FORMATS,
    DatasetQualityGateResult,
    load_report_dataset_rows,
    run_report_dataset_quality_gate,
)
from sp63_core.dataset.report import build_dataset_report, export_dataset_report_json
from sp63_core.dataset.split import (
    DatasetSplit,
    export_dataset_split_csv,
    split_dataset_cases,
)

__all__ = [
    "DATASET_COLUMNS",
    "DATASET_VERSION",
    "DIAGNOSTIC_DATASET_SOURCE",
    "DatasetCase",
    "DatasetQualityGateResult",
    "DatasetSplit",
    "DiagnosticDatasetCase",
    "DiagnosticDatasetSplit",
    "REPORT_DATASET_SOURCE",
    "REQUIRED_REPORT_DATASET_COLUMNS",
    "SUPPORTED_REPORT_DATASET_FORMATS",
    "SUPPORTED_REPORT_QUALITY_FORMATS",
    "ReportDatasetExportResult",
    "build_dataset_report",
    "diagnostic_dataset_warnings",
    "diagnostic_group_leakage_count",
    "diagnostic_status_counts",
    "diagnostic_unique_group_count",
    "export_dataset_csv",
    "export_dataset_from_report_archive",
    "export_dataset_report_json",
    "export_dataset_split_csv",
    "extract_dataset_row_from_report_json",
    "generate_diagnostic_dataset_cases",
    "generate_dataset_cases",
    "load_report_dataset_rows",
    "run_report_dataset_quality_gate",
    "split_diagnostic_dataset_by_group",
    "split_dataset_cases",
]
