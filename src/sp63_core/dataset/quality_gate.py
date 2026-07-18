"""Quality gate for report-derived ML dataset rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset.from_reports import REPORT_DATASET_SOURCE
from sp63_core.dataset.generator import DATASET_VERSION
from sp63_core.report.ed01_contract import public_report_dataset_row_errors
from sp63_core.sections import RectangularBendingOrientation

SUPPORTED_REPORT_QUALITY_FORMATS = ("jsonl", "json", "csv")

PROVENANCE_COLUMNS = (
    "dataset_source",
    "dataset_version",
    "case_id",
    "source_archive_path",
    "report_json_path",
    "input_json_path",
    "manifest_path",
    "input_sha256",
    "report_json_sha256",
    "manifest_sha256",
    "archive_validation_status",
    "status_scope",
    "local_axes_id",
    "moment_axis",
    "tension_face",
    "load_duration",
    "completeness_status",
    "evidence_status",
    "project_use_status",
    "project_use",
)

INPUT_FEATURE_COLUMNS = (
    "b",
    "h",
    "cover",
    "concrete_class",
    "longitudinal_rebar_class",
    "stirrup_rebar_class",
    "M",
    "Q",
)

TARGET_CANDIDATE_COLUMNS = (
    "strength_status",
    "serviceability_status",
    "overall_status",
    "warnings_count",
)

ADVISORY_FLAG_COLUMNS = (
    "requires_engineer_review",
    "ml_is_advisory_only",
    "deterministic_checks_required",
)

REQUIRED_REPORT_DATASET_COLUMNS = (
    *PROVENANCE_COLUMNS,
    *INPUT_FEATURE_COLUMNS,
    *TARGET_CANDIDATE_COLUMNS,
    *ADVISORY_FLAG_COLUMNS,
)

KNOWN_LEAKAGE_COLUMNS = (
    "dataset_version",
    "local_axes_id",
    "bending_status",
    "shear_status",
    "crack_formation_status",
    "crack_width_status",
    "deflection_status",
    "strength_status",
    "serviceability_status",
    "overall_status",
    "failure_reason",
    "project_use",
    "requires_engineer_review",
)


@dataclass(frozen=True)
class DatasetQualityGateResult:
    """Quality gate summary for a report-derived ML dataset."""

    status: str
    source_path: str
    row_count: int
    column_count: int
    required_columns_present: bool
    missing_required_columns: tuple[str, ...]
    empty_critical_values_count: int
    status_distribution: dict[str, int]
    leakage_columns_detected: tuple[str, ...]
    provenance_columns_present: bool
    advisory_flags_present: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def load_report_dataset_rows(
    path: Path,
    dataset_format: str | None = None,
) -> list[dict[str, Any]]:
    """Load report-derived dataset rows from JSONL, JSON, or CSV."""
    source = Path(path)
    data_format = _resolve_dataset_format(source, dataset_format)
    if data_format == "jsonl":
        return _load_jsonl_rows(source)
    if data_format == "json":
        return _load_json_rows(source)
    if data_format == "csv":
        with source.open(newline="", encoding="utf-8") as file:
            return [dict(row) for row in csv.DictReader(file)]
    raise ValueError(
        "dataset_format must be one of: " + ", ".join(SUPPORTED_REPORT_QUALITY_FORMATS)
    )


def run_report_dataset_quality_gate(
    *,
    dataset_path: Path,
    dataset_format: str | None = None,
    task: str = "classification",
    min_rows: int = 100,
    require_status_diversity: bool = True,
) -> DatasetQualityGateResult:
    """Run report-derived dataset quality checks before ML use."""
    if min_rows < 0:
        raise ValueError("min_rows must be non-negative")

    rows = load_report_dataset_rows(dataset_path, dataset_format)
    columns = tuple(sorted({key for row in rows for key in row}))
    missing_required = tuple(
        column for column in REQUIRED_REPORT_DATASET_COLUMNS if column not in columns
    )
    required_columns_present = not missing_required
    provenance_columns_present = all(column in columns for column in PROVENANCE_COLUMNS)
    advisory_flags_present = _advisory_flags_present(rows, columns)
    empty_critical_values_count = _count_empty_critical_values(rows)
    status_distribution = dict(Counter(str(row.get("overall_status")) for row in rows))
    if not rows:
        status_distribution = {}

    leakage_columns = _detect_leakage_columns(columns, task=task)
    warnings: list[str] = []
    errors: list[str] = []

    if not rows:
        errors.append("dataset contains no rows")
    if missing_required:
        errors.append("dataset is missing required columns")
    if not provenance_columns_present:
        errors.append("dataset provenance columns are incomplete")
    if not advisory_flags_present:
        errors.append("dataset advisory flags are missing or false")
    if empty_critical_values_count:
        errors.append("dataset contains empty critical values")
    if any(str(row.get("archive_validation_status")) != "pass" for row in rows):
        errors.append("archive_validation_status must be pass for every row")
    errors.extend(report_dataset_safety_contract_errors(rows))

    if len(rows) < min_rows:
        warnings.append("dataset row count is below the configured minimum")
    if leakage_columns:
        warnings.append(
            "status/check result columns must not be used as input features for predictive ML"
        )
    if require_status_diversity and task == "classification":
        missing_statuses = tuple(
            status
            for status in ("pass", "fail", "review_or_fail")
            if status_distribution.get(status, 0) == 0
        )
        if missing_statuses:
            warnings.append(
                "classification dataset is missing status classes: "
                + ", ".join(missing_statuses)
            )
    if any(str(row.get("external_validation_status")) == "not_provided" for row in rows):
        warnings.append("external validation status is not provided for one or more rows")
    if any(str(row.get("material_verification_status")) == "not_provided" for row in rows):
        warnings.append("material verification status is not provided for one or more rows")

    if errors:
        status = "fail"
    elif warnings:
        status = "review_required"
    else:
        status = "pass"

    return DatasetQualityGateResult(
        status=status,
        source_path=str(dataset_path),
        row_count=len(rows),
        column_count=len(columns),
        required_columns_present=required_columns_present,
        missing_required_columns=missing_required,
        empty_critical_values_count=empty_critical_values_count,
        status_distribution=status_distribution,
        leakage_columns_detected=leakage_columns,
        provenance_columns_present=provenance_columns_present,
        advisory_flags_present=advisory_flags_present,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )


def _resolve_dataset_format(path: Path, dataset_format: str | None) -> str:
    if dataset_format:
        data_format = dataset_format.lower()
    else:
        suffix = path.suffix.lower()
        data_format = {".jsonl": "jsonl", ".json": "json", ".csv": "csv"}.get(suffix, "")
    if data_format not in SUPPORTED_REPORT_QUALITY_FORMATS:
        raise ValueError(
            "dataset_format must be provided as one of: "
            + ", ".join(SUPPORTED_REPORT_QUALITY_FORMATS)
        )
    return data_format


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL rows must be objects: {path}")
        rows.append(value)
    return rows


def _load_json_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("rows"), list):
        value = value["rows"]
    if not isinstance(value, list):
        raise ValueError(f"JSON dataset must contain a list or an object with rows: {path}")
    if not all(isinstance(row, dict) for row in value):
        raise ValueError(f"JSON dataset rows must be objects: {path}")
    return [dict(row) for row in value]


def _count_empty_critical_values(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for column in REQUIRED_REPORT_DATASET_COLUMNS:
            if column not in row:
                continue
            if _is_empty(row[column]):
                count += 1
    return count


def _advisory_flags_present(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> bool:
    if not all(column in columns for column in ADVISORY_FLAG_COLUMNS):
        return False
    return all(
        _is_true(row.get("requires_engineer_review"))
        and _is_true(row.get("ml_is_advisory_only"))
        and _is_true(row.get("deterministic_checks_required"))
        for row in rows
    )


def report_dataset_safety_contract_errors(
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    """Return fail-closed errors for versioned report-dataset provenance."""
    errors: list[str] = []
    if any(row.get("dataset_source") != REPORT_DATASET_SOURCE for row in rows):
        errors.append(
            f"dataset_source must be {REPORT_DATASET_SOURCE!r} for every row"
        )
    if any(row.get("dataset_version") != DATASET_VERSION for row in rows):
        errors.append(
            f"dataset_version must be {DATASET_VERSION!r} for every row"
        )
    if any(not _orientation_is_valid(row) for row in rows):
        errors.append("local-axis orientation provenance is invalid")
    if any(row.get("load_duration") != "short" for row in rows):
        errors.append("load_duration must be short for every row")
    if any(not _hard_safety_statuses_are_valid(row) for row in rows):
        errors.append("hard safety statuses are invalid")
    if any(public_report_dataset_row_errors(row) for row in rows):
        errors.append("ED-01 public report-dataset contract is invalid")
    return tuple(errors)


def _orientation_is_valid(row: dict[str, Any]) -> bool:
    try:
        RectangularBendingOrientation(
            local_axes_id=row.get("local_axes_id"),
            moment_axis=row.get("moment_axis"),
            tension_face=row.get("tension_face"),
        )
    except ValueError:
        return False
    return True


def _hard_safety_statuses_are_valid(row: dict[str, Any]) -> bool:
    return (
        row.get("completeness_status") == "incomplete"
        and row.get("evidence_status") == "needs_engineer_review"
        and row.get("project_use_status") == "prohibited"
        and _is_false(row.get("project_use"))
        and _is_true(row.get("requires_engineer_review"))
    )


def _detect_leakage_columns(columns: tuple[str, ...], *, task: str) -> tuple[str, ...]:
    allowed_targets = {"overall_status"} if task == "classification" else set()
    detected = set()
    for column in columns:
        if column == "archive_validation_status":
            continue
        if column in allowed_targets:
            continue
        if column in KNOWN_LEAKAGE_COLUMNS or column.endswith("_status"):
            detected.add(column)
    return tuple(sorted(detected))


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return False


def _is_false(value: Any) -> bool:
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip().lower() in {"false", "0", "no"}
    return False
