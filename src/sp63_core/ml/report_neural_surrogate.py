"""Advisory-only neural surrogate for leakage-safe report-derived features."""

from __future__ import annotations

import warnings as py_warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import (
    build_report_dataset_feature_set,
    load_report_dataset_rows,
)
from sp63_core.ml.report_baseline import (
    _build_category_encoders,
    _feature_matrix,
    _split_rows,
)


@dataclass(frozen=True)
class ReportNeuralSurrogateResult:
    """Neural surrogate smoke metrics for report-derived ML features."""

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
    neural_network_used: bool
    metrics: dict[str, Any]
    confusion_matrix: list[list[int]]
    feature_columns: tuple[str, ...]
    excluded_leakage_columns: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def build_report_neural_surrogate_result(
    *,
    dataset_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    hidden_layer_sizes: tuple[int, ...] = (16,),
    max_iter: int = 500,
    random_state: int = 42,
) -> ReportNeuralSurrogateResult:
    """Build an advisory neural surrogate smoke report from K45 features."""
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
    neural_network_used = False

    warnings.extend(
        (
            "neural surrogate is advisory-only and must not be used as a design checker",
            "all ML predictions require deterministic SP63 verification",
            "metrics are not production evidence",
        )
    )
    if len(rows) < 100:
        warnings.append("dataset is too small for reliable neural surrogate metrics")
    if feature_mode == "deterministic_derived":
        warnings.append(
            "deterministic-derived features may leak design decisions and must not be used "
            "for project ML decisions without review"
        )

    if not errors and len(feature_set.target_distribution) >= 2:
        train_rows, validation_rows, test_rows = _split_rows(rows, random_state=random_state)
        if not test_rows:
            test_rows = validation_rows or train_rows
        train_count = len(train_rows)
        validation_count = len(validation_rows)
        test_count = len(test_rows)
        (
            metrics,
            confusion,
            model_name,
            neural_network_used,
            model_warning,
        ) = _evaluate_neural_surrogate_classifier(
            train_rows=train_rows,
            test_rows=test_rows,
            feature_columns=feature_set.feature_columns,
            target=target,
            labels=tuple(sorted(feature_set.target_distribution)),
            hidden_layer_sizes=hidden_layer_sizes,
            max_iter=max_iter,
            random_state=random_state,
        )
        if model_warning:
            warnings.append(model_warning)
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

    return ReportNeuralSurrogateResult(
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
        neural_network_used=neural_network_used,
        metrics=metrics,
        confusion_matrix=confusion,
        feature_columns=feature_set.feature_columns,
        excluded_leakage_columns=feature_set.excluded_leakage_columns,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )


def _evaluate_neural_surrogate_classifier(
    *,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    feature_columns: tuple[str, ...],
    target: str,
    labels: tuple[str, ...],
    hidden_layer_sizes: tuple[int, ...],
    max_iter: int,
    random_state: int,
) -> tuple[dict[str, Any], list[list[int]], str, bool, str | None]:
    try:
        from sklearn.exceptions import ConvergenceWarning
        from sklearn.metrics import (
            accuracy_score,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return (
            {},
            [],
            "sklearn_unavailable",
            False,
            "scikit-learn is unavailable; neural surrogate was not trained",
        )

    encoders = _build_category_encoders(train_rows + test_rows, feature_columns)
    train_features = _feature_matrix(train_rows, feature_columns, encoders)
    test_features = _feature_matrix(test_rows, feature_columns, encoders)
    train_target = [str(row[target]) for row in train_rows]
    test_target = [str(row[target]) for row in test_rows]

    if len(set(train_target)) < 2:
        return (
            {},
            [],
            "not_trained_single_class_split",
            False,
            "training split has fewer than two target classes; neural surrogate was not trained",
        )

    classifier = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation="relu",
            solver="adam",
            max_iter=max_iter,
            random_state=random_state,
        ),
    )
    with py_warnings.catch_warnings():
        py_warnings.simplefilter("ignore", ConvergenceWarning)
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
        "hidden_layer_sizes": hidden_layer_sizes,
        "max_iter": max_iter,
    }
    confusion = confusion_matrix(test_target, predictions, labels=labels).tolist()
    return metrics, confusion, "MLPClassifier", True, None
