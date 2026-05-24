"""Dataset generation helpers for the SP 63 MVP."""

from sp63_core.dataset.diagnostic import (
    DIAGNOSTIC_DATASET_SOURCE,
    DiagnosticDatasetCase,
    DiagnosticDatasetSplit,
    diagnostic_dataset_warnings,
    diagnostic_group_leakage_count,
    diagnostic_status_counts,
    generate_diagnostic_dataset_cases,
    split_diagnostic_dataset_by_group,
)
from sp63_core.dataset.generator import (
    DATASET_COLUMNS,
    DATASET_VERSION,
    DatasetCase,
    export_dataset_csv,
    generate_dataset_cases,
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
    "DatasetSplit",
    "DiagnosticDatasetCase",
    "DiagnosticDatasetSplit",
    "build_dataset_report",
    "diagnostic_dataset_warnings",
    "diagnostic_group_leakage_count",
    "diagnostic_status_counts",
    "export_dataset_csv",
    "export_dataset_report_json",
    "export_dataset_split_csv",
    "generate_diagnostic_dataset_cases",
    "generate_dataset_cases",
    "split_diagnostic_dataset_by_group",
    "split_dataset_cases",
]
