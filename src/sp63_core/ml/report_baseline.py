"""Baseline ML report for leakage-safe report-derived features."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import (
    build_report_dataset_feature_set,
    load_report_dataset_rows,
)


@dataclass(frozen=True)
class ReportBaselineMLResult:
    """Baseline classification metrics for report-derived ML features."""

    status: str
    source_dataset: str
    row_count: int
    feature_mode: str
    target: str
    target_distribution: dict[str, int]
    train_count: int
    validation_count: int
    test_count: int
    model_name: str
    metrics: dict[str, Any]
    confusion_matrix: list[list[int]]
    feature_columns: tuple[str, ...]
    excluded_leakage_columns: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    neural_network_used: bool = False


def build_report_baseline_ml_result(
    *,
    dataset_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    random_state: int = 42,
) -> ReportBaselineMLResult:
    """Build a non-neural baseline classification report from K45 features."""
    rows = load_report_dataset_rows(dataset_path, dataset_format)
    feature_set = build_report_dataset_feature_set(
        dataset_path=dataset_path,
        dataset_format=dataset_format,
        target=target,
        feature_mode=feature_mode,
        random_state=random_state,
    )
    warnings = list(feature_set.warnings)
    errors = list(feature_set.errors)
    metrics: dict[str, Any] = {}
    confusion: list[list[int]] = []
    model_name = "not_run"

    if len(rows) < 100:
        warnings.append("dataset is too small for reliable ML metrics")
    if feature_mode == "deterministic_derived":
        warnings.append(
            "deterministic-derived features may leak design decisions and must not be used "
            "for project ML decisions without review"
        )

    if not errors and len(feature_set.target_distribution) >= 2:
        train_rows, validation_rows, test_rows = _split_rows(rows, random_state=random_state)
        if not test_rows:
            test_rows = validation_rows or train_rows
        metrics, confusion, model_name, model_warning = _evaluate_baseline_classifier(
            train_rows=train_rows,
            test_rows=test_rows,
            feature_columns=feature_set.feature_columns,
            target=target,
            labels=tuple(sorted(feature_set.target_distribution)),
            random_state=random_state,
        )
        if model_warning:
            warnings.append(model_warning)
        train_count = len(train_rows)
        validation_count = len(validation_rows)
        test_count = len(test_rows)
    else:
        train_count = feature_set.train_count
        validation_count = feature_set.validation_count
        test_count = feature_set.test_count

    if errors:
        status = "fail"
    elif warnings:
        status = "review_required"
    else:
        status = "pass"

    return ReportBaselineMLResult(
        status=status,
        source_dataset=str(dataset_path),
        row_count=len(rows),
        feature_mode=feature_mode,
        target=target,
        target_distribution=feature_set.target_distribution,
        train_count=train_count,
        validation_count=validation_count,
        test_count=test_count,
        model_name=model_name,
        metrics=metrics,
        confusion_matrix=confusion,
        feature_columns=feature_set.feature_columns,
        excluded_leakage_columns=feature_set.excluded_leakage_columns,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        neural_network_used=False,
    )


def _evaluate_baseline_classifier(
    *,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    feature_columns: tuple[str, ...],
    target: str,
    labels: tuple[str, ...],
    random_state: int,
) -> tuple[dict[str, Any], list[list[int]], str, str | None]:
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    encoders = _build_category_encoders(train_rows + test_rows, feature_columns)
    train_features = _feature_matrix(train_rows, feature_columns, encoders)
    test_features = _feature_matrix(test_rows, feature_columns, encoders)
    train_target = [str(row[target]) for row in train_rows]
    test_target = [str(row[target]) for row in test_rows]
    train_classes = set(train_target)

    if len(train_classes) < 2:
        classifier: Any = DummyClassifier(strategy="most_frequent")
        model_name = "DummyClassifier(strategy='most_frequent')"
        warning = "training split has fewer than two target classes; dummy baseline was used"
    else:
        classifier = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=random_state,
            ),
        )
        model_name = "LogisticRegression"
        warning = None

    classifier.fit(train_features, train_target)
    predictions = classifier.predict(test_features)
    metrics = {
        "accuracy": float(accuracy_score(test_target, predictions)),
        "macro_f1": float(
            f1_score(test_target, predictions, labels=labels, average="macro", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(test_target, predictions, labels=labels, average="weighted", zero_division=0)
        ),
        "precision_macro": float(
            precision_score(
                test_target,
                predictions,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "recall_macro": float(
            recall_score(
                test_target,
                predictions,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "class_distribution": dict(sorted(Counter(test_target).items())),
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
    }
    confusion = confusion_matrix(test_target, predictions, labels=labels).tolist()
    return metrics, confusion, model_name, warning


def _split_rows(
    rows: list[dict[str, Any]],
    *,
    random_state: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    groups = _group_rows(rows)
    keys = sorted(groups)
    random.Random(random_state).shuffle(keys)
    total = len(keys)
    train_group_count = int(total * 0.7)
    validation_group_count = int(total * 0.15)
    if train_group_count == 0 and total:
        train_group_count = 1
    if train_group_count + validation_group_count > total:
        validation_group_count = max(0, total - train_group_count)

    train_keys = keys[:train_group_count]
    validation_keys = keys[train_group_count : train_group_count + validation_group_count]
    test_keys = keys[train_group_count + validation_group_count :]
    return (
        _rows_for_keys(groups, train_keys),
        _rows_for_keys(groups, validation_keys),
        _rows_for_keys(groups, test_keys),
    )


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


def _rows_for_keys(
    groups: dict[str, list[dict[str, Any]]],
    keys: list[str],
) -> list[dict[str, Any]]:
    return [row for key in keys for row in groups[key]]


def _feature_matrix(
    rows: list[dict[str, Any]],
    feature_columns: tuple[str, ...],
    encoders: dict[str, dict[str, float]],
) -> list[list[float]]:
    return [
        [_feature_value(row.get(column), encoders.get(column, {})) for column in feature_columns]
        for row in rows
    ]


def _build_category_encoders(
    rows: list[dict[str, Any]],
    feature_columns: tuple[str, ...],
) -> dict[str, dict[str, float]]:
    encoders: dict[str, dict[str, float]] = {}
    for column in feature_columns:
        values = [row.get(column) for row in rows]
        if any(_is_non_numeric(value) for value in values):
            categories = sorted({str(value) for value in values if not _is_empty(value)})
            encoders[column] = {
                category: float(index + 1) for index, category in enumerate(categories)
            }
    return encoders


def _feature_value(value: Any, encoder: dict[str, float]) -> float:
    if _is_empty(value):
        return 0.0
    if encoder:
        return encoder.get(str(value), 0.0)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return 1.0 if value.strip().lower() == "true" else 0.0
    return float(value)


def _is_non_numeric(value: Any) -> bool:
    if _is_empty(value):
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return True
    return False


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")
