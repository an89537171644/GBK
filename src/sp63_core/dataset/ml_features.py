"""Leakage-safe feature set preparation for report-derived datasets."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset.quality_gate import (
    load_report_dataset_rows,
    report_dataset_safety_contract_errors,
)

SUPPORTED_REPORT_DATASET_TARGETS = (
    "overall_status",
    "strength_status",
    "serviceability_status",
    "bending_status",
    "shear_status",
    "crack_width_status",
    "deflection_status",
)

INPUT_ONLY_FEATURE_COLUMNS = (
    "b",
    "h",
    "cover",
    "concrete_class",
    "longitudinal_rebar_class",
    "stirrup_rebar_class",
    "moment_axis",
    "tension_face",
    "load_duration",
    "M",
    "Q",
    "Mser",
    "span",
    "check_cracks",
    "check_crack_width",
    "check_deflection",
)

DETERMINISTIC_DERIVED_FEATURE_COLUMNS = (
    "h0",
    "longitudinal_as_mm2",
    "transverse_asw_mm2",
    "main_bar_count",
    "main_bar_diameter",
    "stirrup_diameter",
    "stirrup_spacing",
)

EXPLICIT_LEAKAGE_COLUMNS = (
    "dataset_source",
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
    "Mult",
    "Qult",
    "Mcrc",
    "acrc",
    "deflection",
    "bending_utilization",
    "shear_utilization",
    "completeness_status",
    "evidence_status",
    "project_use_status",
    "project_use",
    "requires_engineer_review",
    "ml_is_advisory_only",
    "deterministic_checks_required",
)


@dataclass(frozen=True)
class MLFeatureSetResult:
    """Feature/target/split summary for a report-derived dataset."""

    status: str
    source_path: str
    row_count: int
    feature_count: int
    target: str
    target_distribution: dict[str, int]
    feature_columns: tuple[str, ...]
    target_columns: tuple[str, ...]
    excluded_leakage_columns: tuple[str, ...]
    train_count: int
    validation_count: int
    test_count: int
    split_strategy: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def build_report_dataset_feature_set(
    *,
    dataset_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    split: bool = True,
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> MLFeatureSetResult:
    """Build leakage-safe feature metadata for report-derived rows."""
    rows = load_report_dataset_rows(dataset_path, dataset_format)
    columns = tuple(sorted({key for row in rows for key in row}))
    warnings: list[str] = []
    errors: list[str] = []

    if target not in SUPPORTED_REPORT_DATASET_TARGETS:
        raise ValueError(
            "target must be one of: " + ", ".join(SUPPORTED_REPORT_DATASET_TARGETS)
        )
    if feature_mode not in {"input_only", "deterministic_derived"}:
        raise ValueError("feature_mode must be one of: input_only, deterministic_derived")
    _validate_split_ratios(train_ratio, validation_ratio, test_ratio)

    if not rows:
        errors.append("dataset contains no rows")
    errors.extend(report_dataset_safety_contract_errors(rows))

    target_columns = (target,) if target in columns else ()
    if target not in columns:
        errors.append(f"target column is missing: {target}")
    target_values = [row.get(target) for row in rows if target in row]
    if any(_is_empty(value) for value in target_values):
        errors.append(f"target column contains empty values: {target}")
    target_distribution = dict(
        Counter(str(value) for value in target_values if not _is_empty(value))
    )

    feature_columns = _select_feature_columns(rows, feature_mode)
    excluded_leakage_columns = detect_leakage_columns(columns, target)
    if not feature_columns:
        errors.append("no feature columns selected")

    if feature_mode == "deterministic_derived":
        warnings.append(
            "deterministic-derived features may leak design decisions "
            "and must be reviewed before ML use"
        )
    if len(rows) < 100:
        warnings.append("dataset is too small for reliable ML training")
    if len(target_distribution) == 1:
        warnings.append("target column is constant and requires review before classification ML")

    train_count, validation_count, test_count, split_strategy = _split_counts(
        rows=rows,
        split=split,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
        random_state=random_state,
    )

    if errors:
        status = "fail"
    elif warnings:
        status = "review_required"
    else:
        status = "pass"

    return MLFeatureSetResult(
        status=status,
        source_path=str(dataset_path),
        row_count=len(rows),
        feature_count=len(feature_columns),
        target=target,
        target_distribution=target_distribution,
        feature_columns=feature_columns,
        target_columns=target_columns,
        excluded_leakage_columns=excluded_leakage_columns,
        train_count=train_count,
        validation_count=validation_count,
        test_count=test_count,
        split_strategy=split_strategy,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )


def select_input_only_features(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    """Select input-only feature columns available in the loaded rows."""
    columns = {key for row in rows for key in row}
    return tuple(column for column in INPUT_ONLY_FEATURE_COLUMNS if column in columns)


def detect_leakage_columns(columns: Iterable[str], target: str) -> tuple[str, ...]:
    """Return columns that must be excluded from input features."""
    detected = set()
    for column in columns:
        if column == target:
            continue
        if column == "archive_validation_status":
            continue
        if column in EXPLICIT_LEAKAGE_COLUMNS or column.endswith("_status"):
            detected.add(column)
    return tuple(sorted(detected))


def _select_feature_columns(rows: list[dict[str, Any]], feature_mode: str) -> tuple[str, ...]:
    input_features = select_input_only_features(rows)
    if feature_mode == "input_only":
        return input_features
    columns = {key for row in rows for key in row}
    derived = tuple(
        column for column in DETERMINISTIC_DERIVED_FEATURE_COLUMNS if column in columns
    )
    return (*input_features, *derived)


def _split_counts(
    *,
    rows: list[dict[str, Any]],
    split: bool,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
    random_state: int,
) -> tuple[int, int, int, str]:
    if not split:
        return len(rows), 0, 0, "none"
    if not rows:
        return 0, 0, 0, "source_archive_path_case_id"

    groups = _group_rows(rows)
    keys = sorted(groups)
    random.Random(random_state).shuffle(keys)
    total_groups = len(keys)
    ratio_sum = train_ratio + validation_ratio + test_ratio
    train_group_count = int(total_groups * train_ratio / ratio_sum)
    validation_group_count = int(total_groups * validation_ratio / ratio_sum)
    if train_group_count == 0 and total_groups:
        train_group_count = 1
    if train_group_count + validation_group_count > total_groups:
        validation_group_count = max(0, total_groups - train_group_count)

    train_keys = set(keys[:train_group_count])
    validation_keys = set(keys[train_group_count : train_group_count + validation_group_count])
    test_keys = set(keys[train_group_count + validation_group_count :])

    train_count = sum(len(groups[key]) for key in train_keys)
    validation_count = sum(len(groups[key]) for key in validation_keys)
    test_count = sum(len(groups[key]) for key in test_keys)
    return train_count, validation_count, test_count, "source_archive_path_case_id"


def _group_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        case_id = row.get("case_id")
        source_archive = row.get("source_archive_path")
        if case_id or source_archive:
            group_key = f"{source_archive or 'unknown_archive'}|{case_id or 'unknown_case'}"
        else:
            group_key = f"row_{index:06d}"
        groups[group_key].append(row)
    return dict(groups)


def _validate_split_ratios(train_ratio: float, validation_ratio: float, test_ratio: float) -> None:
    ratios = (train_ratio, validation_ratio, test_ratio)
    if any(ratio < 0 for ratio in ratios):
        raise ValueError("split ratios must be non-negative")
    if sum(ratios) <= 0:
        raise ValueError("at least one split ratio must be positive")


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")
