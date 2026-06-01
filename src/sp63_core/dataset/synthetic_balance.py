"""Balance/readiness checks for synthetic report-derived datasets."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset.ml_features import (
    INPUT_ONLY_FEATURE_COLUMNS,
    SUPPORTED_REPORT_DATASET_TARGETS,
    detect_leakage_columns,
)
from sp63_core.dataset.quality_gate import (
    REQUIRED_REPORT_DATASET_COLUMNS,
    load_report_dataset_rows,
)

OVERALL_STATUS_REQUIRED_CLASSES = ("pass", "fail", "review_or_fail")


@dataclass(frozen=True)
class SyntheticDatasetBalanceResult:
    """Balance and stratified-readiness summary for a synthetic dataset."""

    status: str
    source_dataset: str
    row_count: int
    target: str
    target_distribution: dict[str, int]
    target_distribution_ratio: dict[str, float]
    min_class_count: int
    max_class_count: int
    imbalance_ratio: float
    required_classes_present: bool
    missing_required_classes: tuple[str, ...]
    stratified_split_ready: bool
    train_count: int
    validation_count: int
    test_count: int
    class_counts_by_split: dict[str, dict[str, int]]
    leakage_columns_detected: tuple[str, ...]
    recommendations: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def analyze_synthetic_dataset_balance(
    *,
    dataset_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    min_rows: int = 100,
    min_class_count: int = 20,
    max_imbalance_ratio: float = 3.0,
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> SyntheticDatasetBalanceResult:
    """Analyze status-class balance and split readiness for synthetic rows."""
    if target not in SUPPORTED_REPORT_DATASET_TARGETS:
        raise ValueError(
            "target must be one of: " + ", ".join(SUPPORTED_REPORT_DATASET_TARGETS)
        )
    if min_rows < 0:
        raise ValueError("min_rows must be non-negative")
    if min_class_count < 0:
        raise ValueError("min_class_count must be non-negative")
    if max_imbalance_ratio < 1:
        raise ValueError("max_imbalance_ratio must be at least 1")

    rows = load_report_dataset_rows(dataset_path, dataset_format)
    columns = tuple(sorted({key for row in rows for key in row}))
    missing_required_columns = tuple(
        column for column in REQUIRED_REPORT_DATASET_COLUMNS if column not in columns
    )
    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        errors.append("dataset contains no rows")
    if missing_required_columns:
        errors.append("dataset is missing required columns")
    if target not in columns:
        errors.append(f"target column is missing: {target}")

    empty_critical_values_count = _count_empty_critical_values(rows)
    if empty_critical_values_count:
        errors.append("dataset contains empty critical values")
    if any(str(row.get("archive_validation_status")) != "pass" for row in rows):
        errors.append("archive_validation_status must be pass for every row")
    if not _advisory_flags_present(rows):
        errors.append("dataset advisory flags are missing or false")

    target_values = _target_values(rows, target)
    if any(_is_empty(row.get(target)) for row in rows if target in row):
        errors.append(f"target column contains empty values: {target}")

    target_distribution = dict(Counter(target_values))
    target_distribution_ratio = _distribution_ratio(target_distribution, len(target_values))
    nonzero_counts = [count for count in target_distribution.values() if count > 0]
    actual_min_class_count = min(nonzero_counts, default=0)
    actual_max_class_count = max(nonzero_counts, default=0)
    imbalance_ratio = (
        actual_max_class_count / actual_min_class_count if actual_min_class_count else 0.0
    )

    missing_required_classes = _missing_required_classes(target, target_distribution)
    required_classes_present = not missing_required_classes

    split_summary = build_stratified_split_summary(
        rows=rows,
        target=target,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
        test_ratio=test_ratio,
        random_state=random_state,
    )
    class_counts_by_split = split_summary["class_counts_by_split"]
    stratified_split_ready = bool(split_summary["stratified_split_ready"])

    leakage_columns = detect_leakage_columns(columns, target)
    input_feature_columns = tuple(
        column for column in INPUT_ONLY_FEATURE_COLUMNS if column in columns
    )
    leakage_in_input_features = tuple(
        column for column in leakage_columns if column in input_feature_columns
    )
    if leakage_in_input_features:
        errors.append("leakage columns are included in input-only feature columns")

    if len(rows) < min_rows:
        warnings.append("dataset row count is below the configured minimum")
    if len(target_distribution) == 1:
        warnings.append("target column is constant and requires review before ML")
    elif len(target_distribution) < 2 and rows:
        warnings.append("target column has too few classes for classification ML")
    if missing_required_classes:
        warnings.append(
            "dataset is missing required target classes: "
            + ", ".join(missing_required_classes)
        )
    if actual_min_class_count and actual_min_class_count < min_class_count:
        warnings.append("minimum class count is below the configured threshold")
    if imbalance_ratio and imbalance_ratio > max_imbalance_ratio:
        warnings.append("target class imbalance exceeds the configured threshold")
    if not stratified_split_ready and rows and target in columns:
        warnings.append("stratified split cannot preserve all target classes")
    if any(str(row.get("external_validation_status")) == "not_provided" for row in rows):
        warnings.append("external validation status is not provided for one or more rows")
    if any(str(row.get("material_verification_status")) == "not_provided" for row in rows):
        warnings.append("material verification status is not provided for one or more rows")

    recommendations = _build_recommendations(
        row_count=len(rows),
        min_rows=min_rows,
        target_distribution=target_distribution,
        missing_required_classes=missing_required_classes,
        min_class_count=actual_min_class_count,
        configured_min_class_count=min_class_count,
        imbalance_ratio=imbalance_ratio,
        max_imbalance_ratio=max_imbalance_ratio,
        rows=rows,
    )

    if errors:
        status = "fail"
    elif warnings:
        status = "review_required"
    else:
        status = "pass"

    return SyntheticDatasetBalanceResult(
        status=status,
        source_dataset=str(dataset_path),
        row_count=len(rows),
        target=target,
        target_distribution=target_distribution,
        target_distribution_ratio=target_distribution_ratio,
        min_class_count=actual_min_class_count,
        max_class_count=actual_max_class_count,
        imbalance_ratio=imbalance_ratio,
        required_classes_present=required_classes_present,
        missing_required_classes=missing_required_classes,
        stratified_split_ready=stratified_split_ready,
        train_count=int(split_summary["train_count"]),
        validation_count=int(split_summary["validation_count"]),
        test_count=int(split_summary["test_count"]),
        class_counts_by_split=class_counts_by_split,
        leakage_columns_detected=leakage_columns,
        recommendations=recommendations,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def build_stratified_split_summary(
    *,
    rows: list[dict[str, Any]],
    target: str,
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> dict[str, Any]:
    """Build deterministic stratified split ids and per-split class counts."""
    _validate_split_ratios(train_ratio, validation_ratio, test_ratio)
    splits = {
        "train": [],
        "validation": [],
        "test": [],
    }
    class_counts_by_split: dict[str, dict[str, int]] = {
        "train": {},
        "validation": {},
        "test": {},
    }
    if not rows or any(target not in row or _is_empty(row.get(target)) for row in rows):
        return {
            "split_strategy": "stratified_by_target",
            "target": target,
            "train": (),
            "validation": (),
            "test": (),
            "train_count": 0,
            "validation_count": 0,
            "test_count": 0,
            "class_counts_by_split": class_counts_by_split,
            "stratified_split_ready": False,
        }

    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_class[str(row[target])].append(row)

    rng = random.Random(random_state)
    for class_name in sorted(by_class):
        class_rows = list(by_class[class_name])
        rng.shuffle(class_rows)
        split_counts = _split_counts_for_class(
            len(class_rows),
            train_ratio=train_ratio,
            validation_ratio=validation_ratio,
            test_ratio=test_ratio,
        )
        train_end = split_counts["train"]
        validation_end = train_end + split_counts["validation"]
        split_rows = {
            "train": class_rows[:train_end],
            "validation": class_rows[train_end:validation_end],
            "test": class_rows[validation_end:],
        }
        for split_name, assigned_rows in split_rows.items():
            splits[split_name].extend(
                _row_identifier(row, index) for index, row in enumerate(assigned_rows)
            )
            if assigned_rows:
                class_counts_by_split[split_name][class_name] = len(assigned_rows)

    for split_name in splits:
        splits[split_name] = sorted(splits[split_name])

    target_classes = set(by_class)
    positive_split_names = {
        split_name
        for split_name, ratio in (
            ("train", train_ratio),
            ("validation", validation_ratio),
            ("test", test_ratio),
        )
        if ratio > 0
    }
    stratified_split_ready = all(
        class_counts_by_split[split_name].get(class_name, 0) > 0
        for class_name in target_classes
        for split_name in positive_split_names
    )

    return {
        "split_strategy": "stratified_by_target",
        "target": target,
        "train": tuple(splits["train"]),
        "validation": tuple(splits["validation"]),
        "test": tuple(splits["test"]),
        "train_count": len(splits["train"]),
        "validation_count": len(splits["validation"]),
        "test_count": len(splits["test"]),
        "class_counts_by_split": class_counts_by_split,
        "stratified_split_ready": stratified_split_ready,
    }


def _split_counts_for_class(
    class_count: int,
    *,
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
) -> dict[str, int]:
    ratio_sum = train_ratio + validation_ratio + test_ratio
    split_ratios = {
        "train": train_ratio,
        "validation": validation_ratio,
        "test": test_ratio,
    }
    positive_splits = [name for name, ratio in split_ratios.items() if ratio > 0]
    raw = {
        name: class_count * ratio / ratio_sum if ratio_sum else 0.0
        for name, ratio in split_ratios.items()
    }
    counts = {name: int(value) for name, value in raw.items()}
    remaining = class_count - sum(counts.values())
    for name, _ in sorted(
        raw.items(),
        key=lambda item: (item[1] - int(item[1]), split_ratios[item[0]]),
        reverse=True,
    ):
        if remaining <= 0:
            break
        counts[name] += 1
        remaining -= 1

    if class_count >= len(positive_splits):
        for name in positive_splits:
            if counts[name] == 0:
                donor = max(positive_splits, key=lambda split_name: counts[split_name])
                if counts[donor] > 1:
                    counts[donor] -= 1
                    counts[name] += 1
    return counts


def _missing_required_classes(target: str, distribution: dict[str, int]) -> tuple[str, ...]:
    if target != "overall_status":
        return ()
    return tuple(
        class_name
        for class_name in OVERALL_STATUS_REQUIRED_CLASSES
        if distribution.get(class_name, 0) == 0
    )


def _distribution_ratio(distribution: dict[str, int], total: int) -> dict[str, float]:
    if total <= 0:
        return {}
    return {
        class_name: count / total
        for class_name, count in sorted(distribution.items())
    }


def _target_values(rows: list[dict[str, Any]], target: str) -> list[str]:
    return [
        str(row[target])
        for row in rows
        if target in row and not _is_empty(row.get(target))
    ]


def _count_empty_critical_values(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for column in REQUIRED_REPORT_DATASET_COLUMNS:
            if column in row and _is_empty(row[column]):
                count += 1
    return count


def _advisory_flags_present(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        _is_true(row.get("requires_engineer_review"))
        and _is_true(row.get("ml_is_advisory_only"))
        and _is_true(row.get("deterministic_checks_required"))
        for row in rows
    )


def _build_recommendations(
    *,
    row_count: int,
    min_rows: int,
    target_distribution: dict[str, int],
    missing_required_classes: tuple[str, ...],
    min_class_count: int,
    configured_min_class_count: int,
    imbalance_ratio: float,
    max_imbalance_ratio: float,
    rows: list[dict[str, Any]],
) -> tuple[str, ...]:
    recommendations: list[str] = []
    if row_count < min_rows:
        recommendations.append(f"increase synthetic case count to at least {min_rows}")
    if "review_or_fail" in missing_required_classes:
        recommendations.append(
            "adjust synthetic input ranges to generate serviceability review cases"
        )
    if target_distribution.get("pass", 0) < configured_min_class_count:
        recommendations.append("include more low-load / larger-section cases")
    if target_distribution.get("fail", 0) < configured_min_class_count:
        recommendations.append("include more high-load / smaller-section cases")
    if _serviceability_review_or_fail_count(rows) < configured_min_class_count:
        recommendations.append(
            "increase span and service moment combinations for serviceability checks"
        )
    if min_class_count and min_class_count < configured_min_class_count:
        recommendations.append("generate additional minority-class cases")
    if imbalance_ratio and imbalance_ratio > max_imbalance_ratio:
        recommendations.append(
            "use stratified sampling or generate additional minority-class cases"
        )
    return tuple(dict.fromkeys(recommendations))


def _serviceability_review_or_fail_count(rows: list[dict[str, Any]]) -> int:
    return sum(
        1
        for row in rows
        if str(row.get("serviceability_status")) in {"fail", "review_or_fail"}
    )


def _row_identifier(row: dict[str, Any], fallback_index: int) -> str:
    case_id = row.get("case_id")
    if case_id:
        return str(case_id)
    input_json_path = row.get("input_json_path")
    if input_json_path:
        return str(input_json_path)
    return f"row_{fallback_index:06d}"


def _validate_split_ratios(train_ratio: float, validation_ratio: float, test_ratio: float) -> None:
    ratios = (train_ratio, validation_ratio, test_ratio)
    if any(ratio < 0 for ratio in ratios):
        raise ValueError("split ratios must be non-negative")
    if sum(ratios) <= 0:
        raise ValueError("at least one split ratio must be positive")


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
