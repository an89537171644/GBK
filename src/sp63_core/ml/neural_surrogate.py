"""Advisory-only neural surrogate smoke report for deterministic datasets."""

import math
import random
import warnings
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sp63_core.dataset import (
    DatasetCase,
    DiagnosticDatasetCase,
    generate_dataset_cases,
    generate_diagnostic_dataset_cases,
    split_diagnostic_dataset_by_group,
)
from sp63_core.ml.baseline_report import (
    EXPANDED_DIAGNOSTIC_INPUT_FEATURES,
    SAFE_REGRESSION_FEATURES,
    SAFE_REGRESSION_TARGETS,
)

NEURAL_SURROGATE_WARNINGS: tuple[str, ...] = (
    "neural surrogate is a smoke MVP and must not be used as a design checker",
    "all ML predictions require deterministic SP63 verification",
    "diagnostic dataset is synthetic and requires engineer review",
    "metrics are not production evidence",
)


@dataclass(frozen=True)
class NeuralSurrogateReport:
    """Metrics for the K29 advisory-only neural surrogate smoke MVP."""

    status: str
    dataset_name: str
    total_rows: int
    train_rows: int
    test_rows: int
    group_key_present: bool
    group_leakage_count: int
    classification_target: str
    classification_metrics: dict[str, Any]
    regression_metrics: dict[str, Any]
    warnings: tuple[str, ...]
    ml_is_advisory_only: bool = True
    neural_network_used: bool = True
    deterministic_checks_required: bool = True
    requires_engineer_review: bool = True


def build_neural_surrogate_report(
    *,
    diagnostic_limit: int = 5000,
    random_state: int = 42,
) -> NeuralSurrogateReport:
    """Build a minimal neural surrogate smoke report without saving a model."""
    if diagnostic_limit < 6:
        raise ValueError("diagnostic_limit must be at least 6")

    diagnostic_cases = generate_diagnostic_dataset_cases(limit=diagnostic_limit)
    split = split_diagnostic_dataset_by_group(diagnostic_cases, seed=random_state)
    train_cases = split.train
    test_cases = split.test
    if not train_cases or not test_cases:
        train_cases, test_cases = _row_train_test_split(
            tuple(diagnostic_cases),
            seed=random_state,
        )

    class_distribution = dict(
        sorted(Counter(case.overall_status for case in diagnostic_cases).items())
    )
    warnings = list(NEURAL_SURROGATE_WARNINGS)
    if len(class_distribution) < 2:
        warnings.append(
            "classification target is constant; neural surrogate cannot be evaluated"
        )
        status = "fail"
        classification_metrics = {
            "target": "overall_status",
            "class_distribution": class_distribution,
            "feature_columns": EXPANDED_DIAGNOSTIC_INPUT_FEATURES,
            "model": "MLPClassifier",
            "status": "fail",
        }
    else:
        classification_metrics = _build_classification_metrics(
            train_cases=train_cases,
            test_cases=test_cases,
            labels=tuple(sorted(class_distribution)),
            random_state=random_state,
        )
        status = "review_required"

    safe_cases = generate_dataset_cases(
        limit=_safe_regression_limit(diagnostic_limit),
        load_duration="short",
        seed=random_state,
    )
    regression_metrics = _build_regression_metrics(
        safe_cases=safe_cases,
        random_state=random_state,
    )

    return NeuralSurrogateReport(
        status=status,
        dataset_name="k28_diagnostic_and_safe_deterministic",
        total_rows=len(diagnostic_cases),
        train_rows=len(train_cases),
        test_rows=len(test_cases),
        group_key_present=all(case.group_key for case in diagnostic_cases),
        group_leakage_count=split.group_leakage_count,
        classification_target="overall_status",
        classification_metrics=classification_metrics,
        regression_metrics=regression_metrics,
        warnings=tuple(warnings),
    )


def _build_classification_metrics(
    *,
    train_cases: Sequence[DiagnosticDatasetCase],
    test_cases: Sequence[DiagnosticDatasetCase],
    labels: tuple[str, ...],
    random_state: int,
) -> dict[str, Any]:
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

    train_features = [_diagnostic_feature_vector(case) for case in train_cases]
    test_features = [_diagnostic_feature_vector(case) for case in test_cases]
    train_target = [case.overall_status for case in train_cases]
    test_target = [case.overall_status for case in test_cases]

    classifier = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(8,),
            max_iter=60,
            random_state=random_state,
        ),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        classifier.fit(train_features, train_target)
    predicted = classifier.predict(test_features)

    return {
        "target": "overall_status",
        "model": "MLPClassifier",
        "feature_mode": "input_only_features",
        "feature_columns": EXPANDED_DIAGNOSTIC_INPUT_FEATURES,
        "deterministic_derived_features_used": False,
        "class_distribution": dict(
            sorted(Counter(train_target + test_target).items())
        ),
        "accuracy": float(accuracy_score(test_target, predicted)),
        "macro_f1": float(
            f1_score(test_target, predicted, labels=labels, average="macro")
        ),
        "per_class_precision": dict(
            zip(
                labels,
                (
                    float(value)
                    for value in precision_score(
                        test_target,
                        predicted,
                        labels=labels,
                        average=None,
                        zero_division=0,
                    )
                ),
                strict=True,
            )
        ),
        "per_class_recall": dict(
            zip(
                labels,
                (
                    float(value)
                    for value in recall_score(
                        test_target,
                        predicted,
                        labels=labels,
                        average=None,
                        zero_division=0,
                    )
                ),
                strict=True,
            )
        ),
        "confusion_matrix": confusion_matrix(
            test_target,
            predicted,
            labels=labels,
        ).tolist(),
        "labels": labels,
    }


def _build_regression_metrics(
    *,
    safe_cases: Sequence[DatasetCase],
    random_state: int,
) -> dict[str, Any]:
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    train_cases, test_cases = _row_train_test_split(tuple(safe_cases), seed=random_state)
    train_features = [_safe_feature_vector(case) for case in train_cases]
    test_features = [_safe_feature_vector(case) for case in test_cases]

    metrics: dict[str, Any] = {
        "dataset": "safe_accepted_deterministic_sp63_core",
        "feature_columns": SAFE_REGRESSION_FEATURES,
        "targets": SAFE_REGRESSION_TARGETS,
        "train_rows": len(train_cases),
        "test_rows": len(test_cases),
        "models": {"mlp": "MLPRegressor"},
    }
    for target_name in SAFE_REGRESSION_TARGETS:
        train_target = [_safe_target(case, target_name) for case in train_cases]
        test_target = [_safe_target(case, target_name) for case in test_cases]
        regressor = make_pipeline(
            StandardScaler(),
            MLPRegressor(
                hidden_layer_sizes=(8,),
                max_iter=80,
                early_stopping=True,
                n_iter_no_change=8,
                random_state=random_state,
            ),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            regressor.fit(train_features, train_target)
        predicted = regressor.predict(test_features)
        mse = float(mean_squared_error(test_target, predicted))
        metrics[target_name] = {
            "mae": float(mean_absolute_error(test_target, predicted)),
            "rmse": math.sqrt(mse),
            "r2": float(r2_score(test_target, predicted)),
        }
    return metrics


def _diagnostic_feature_vector(case: DiagnosticDatasetCase) -> list[float]:
    return [
        _diagnostic_feature_value(case, feature_name)
        for feature_name in EXPANDED_DIAGNOSTIC_INPUT_FEATURES
    ]


def _diagnostic_feature_value(
    case: DiagnosticDatasetCase,
    feature_name: str,
) -> float:
    if feature_name == "concrete_class_code":
        return _class_code(case.concrete_class)
    if feature_name == "main_rebar_class_code":
        return _class_code(case.main_rebar_class)
    if feature_name == "stirrup_rebar_class_code":
        return _class_code(case.stirrup_rebar_class)
    value = getattr(case, feature_name)
    if value is None:
        return 0.0
    return float(value)


def _safe_feature_vector(case: DatasetCase) -> list[float]:
    return [
        float(case.section_b_mm),
        float(case.section_h_mm),
        float(case.cover_mm),
        float(case.moment_nmm),
        float(case.shear_n),
        float(case.moment_service_nmm),
        float(case.span_mm),
        _class_code(case.concrete_class),
        _class_code(case.main_rebar_class),
        _class_code(case.stirrup_rebar_class),
    ]


def _safe_target(case: DatasetCase, target_name: str) -> float:
    if target_name == "longitudinal_as_mm2":
        return float(case.longitudinal_as_mm2)
    if target_name == "bending_utilization":
        return float(case.bending_utilization)
    raise ValueError(f"unsupported regression target {target_name!r}")


def _row_train_test_split(
    cases: tuple[Any, ...],
    *,
    seed: int,
) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    if len(cases) < 2:
        return cases, cases
    shuffled = list(cases)
    random.Random(seed).shuffle(shuffled)
    train_count = max(1, int(len(shuffled) * 0.7))
    if train_count >= len(shuffled):
        train_count = len(shuffled) - 1
    return tuple(shuffled[:train_count]), tuple(shuffled[train_count:])


def _safe_regression_limit(diagnostic_limit: int) -> int:
    return min(max(100, diagnostic_limit // 10), 500)


def _class_code(class_name: str) -> float:
    digits = "".join(character for character in class_name if character.isdigit())
    if not digits:
        raise ValueError(f"cannot derive numeric class code from {class_name!r}")
    return float(digits)
