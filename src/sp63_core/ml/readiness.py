"""ML readiness checks for deterministic dataset rows."""

import random
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

FEATURE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "section_b_mm",
    "section_h_mm",
    "effective_depth_mm",
    "cover_mm",
    "main_bar_diameter_mm",
    "stirrup_diameter_mm",
    "stirrup_spacing_mm",
    "concrete_class",
    "main_rebar_class",
    "stirrup_rebar_class",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
)
RESULT_REQUIRED_COLUMNS: tuple[str, ...] = (
    "longitudinal_as_mm2",
    "transverse_asw_mm2",
    "bending_mult_nmm",
    "shear_qult_n",
    "mcrc_nmm",
    "crack_width_mm",
    "deflection_mm",
)
STATUS_COLUMNS: tuple[str, ...] = (
    "bending_status",
    "shear_status",
    "crack_formation_status",
    "crack_width_status",
    "deflection_status",
    "strength_status",
    "serviceability_status",
    "overall_status",
)
SERVICE_REQUIRED_COLUMNS: tuple[str, ...] = (
    "group_key",
    "warnings_count",
    "requires_engineer_review",
    "unsafe_row",
    "dataset_source",
)
REQUIRED_COLUMNS: tuple[str, ...] = (
    FEATURE_REQUIRED_COLUMNS
    + RESULT_REQUIRED_COLUMNS
    + STATUS_COLUMNS
    + SERVICE_REQUIRED_COLUMNS
)
TARGET_COLUMNS: tuple[str, ...] = RESULT_REQUIRED_COLUMNS + STATUS_COLUMNS
DIAGNOSTIC_DATASET_SOURCE = "diagnostic_deterministic_sp63_core"
DIAGNOSTIC_REQUIRED_OVERALL_STATUSES = ("pass", "fail", "review_or_fail")
DIAGNOSTIC_MIN_CLASSIFICATION_ROWS = 1000
DIAGNOSTIC_MIN_UNIQUE_GROUPS = 50


@dataclass(frozen=True)
class MLReadinessReport:
    """Summary of dataset readiness for later advisory ML work."""

    total_rows: int
    feature_columns_count: int
    target_columns_count: int
    missing_required_columns: tuple[str, ...]
    status_counts: dict[str, dict[str, int]]
    failure_reason_counts: dict[str, int]
    group_key_present: bool
    unique_group_count: int
    unsafe_rows_count: int
    group_leakage_count: int
    constant_target_columns: tuple[str, ...]
    low_variance_status_columns: tuple[str, ...]
    warnings: tuple[str, ...]
    status: str
    requires_engineer_review: bool = True


def build_ml_readiness_report(rows: Iterable[Mapping[str, Any]]) -> MLReadinessReport:
    """Build an ML readiness report for deterministic dataset rows."""
    normalized_rows = tuple(dict(row) for row in rows)
    total_rows = len(normalized_rows)
    missing_required_columns = _missing_required_columns(normalized_rows)
    status_counts = _status_counts(normalized_rows)
    failure_reason_counts = _failure_reason_counts(normalized_rows)
    group_key_present = bool(normalized_rows) and all(
        row.get("group_key") not in (None, "") for row in normalized_rows
    )
    unique_group_count = _unique_group_count(normalized_rows) if group_key_present else 0
    unsafe_rows_count = sum(
        1 for row in normalized_rows if _is_truthy(row.get("unsafe_row", False))
    )
    group_leakage_count = _group_leakage_count(normalized_rows) if group_key_present else 0
    constant_target_columns = _constant_columns(normalized_rows, TARGET_COLUMNS)
    low_variance_status_columns = _constant_columns(normalized_rows, STATUS_COLUMNS)

    warnings: list[str] = []
    diagnostic_dataset = _is_diagnostic_dataset(normalized_rows)
    if total_rows == 0:
        warnings.append("dataset must contain at least one row")
    if missing_required_columns:
        warnings.append(
            "dataset is missing required columns: "
            + ", ".join(missing_required_columns)
        )
    if unsafe_rows_count > 0:
        warnings.append("dataset contains unsafe rows")
    if group_leakage_count > 0:
        warnings.append("dataset split contains group_key leakage")
    if status_counts.get("overall_status") == {"pass": total_rows}:
        warnings.append(
            "dataset contains only passing overall_status rows; "
            "classification ML is not ready without fail/review cases"
        )
    if constant_target_columns:
        warnings.append(
            "dataset contains constant target/status columns; "
            "review target variability before ML training"
        )
    if diagnostic_dataset:
        overall_counts = status_counts.get("overall_status", {})
        missing_statuses = [
            status
            for status in DIAGNOSTIC_REQUIRED_OVERALL_STATUSES
            if status not in overall_counts
        ]
        if missing_statuses:
            warnings.append(
                "diagnostic dataset is missing overall_status values: "
                + ", ".join(missing_statuses)
            )
        if not group_key_present:
            warnings.append("diagnostic dataset is missing group_key values")
        if unique_group_count < DIAGNOSTIC_MIN_UNIQUE_GROUPS:
            warnings.append(
                "diagnostic dataset has fewer than 50 unique group_key values; "
                "group-diverse ML validation remains review-only"
            )
        if total_rows < DIAGNOSTIC_MIN_CLASSIFICATION_ROWS:
            warnings.append(
                "diagnostic dataset has fewer than 1000 rows; "
                "classification readiness remains review-only"
            )

    if total_rows == 0 or missing_required_columns or group_leakage_count > 0:
        status = "fail"
    elif unsafe_rows_count > 0 or constant_target_columns:
        status = "review_required"
    else:
        status = "pass"

    return MLReadinessReport(
        total_rows=total_rows,
        feature_columns_count=len(FEATURE_REQUIRED_COLUMNS),
        target_columns_count=len(TARGET_COLUMNS),
        missing_required_columns=missing_required_columns,
        status_counts=status_counts,
        failure_reason_counts=failure_reason_counts,
        group_key_present=group_key_present,
        unique_group_count=unique_group_count,
        unsafe_rows_count=unsafe_rows_count,
        group_leakage_count=group_leakage_count,
        constant_target_columns=constant_target_columns,
        low_variance_status_columns=low_variance_status_columns,
        warnings=tuple(warnings),
        status=status,
        requires_engineer_review=True,
    )


def _missing_required_columns(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    if not rows:
        return REQUIRED_COLUMNS
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if any(column not in row for row in rows)
    ]
    return tuple(missing)


def _status_counts(rows: tuple[dict[str, Any], ...]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for column in STATUS_COLUMNS:
        counter = Counter(str(row[column]) for row in rows if column in row)
        counts[column] = dict(sorted(counter.items()))
    return counts


def _failure_reason_counts(rows: tuple[dict[str, Any], ...]) -> dict[str, int]:
    counter = Counter(
        str(row["failure_reason"])
        for row in rows
        if row.get("failure_reason") not in (None, "")
    )
    return dict(sorted(counter.items()))


def _group_leakage_count(rows: tuple[dict[str, Any], ...]) -> int:
    groups = sorted({str(row["group_key"]) for row in rows if row.get("group_key")})
    if len(groups) < 2:
        return 0
    shuffled = list(groups)
    random.Random(42).shuffle(shuffled)
    train_count = max(1, int(len(shuffled) * 0.7))
    if train_count >= len(shuffled):
        train_count = len(shuffled) - 1
    train_groups = set(shuffled[:train_count])
    test_groups = set(shuffled[train_count:])
    return len(train_groups & test_groups)


def _unique_group_count(rows: tuple[dict[str, Any], ...]) -> int:
    return len({str(row["group_key"]) for row in rows if row.get("group_key")})


def _constant_columns(
    rows: tuple[dict[str, Any], ...],
    columns: tuple[str, ...],
) -> tuple[str, ...]:
    if not rows:
        return ()
    constant_columns: list[str] = []
    for column in columns:
        values = {row[column] for row in rows if column in row}
        if len(values) == 1:
            constant_columns.append(column)
    return tuple(constant_columns)


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _is_diagnostic_dataset(rows: tuple[dict[str, Any], ...]) -> bool:
    return bool(rows) and all(
        row.get("dataset_source") == DIAGNOSTIC_DATASET_SOURCE for row in rows
    )
