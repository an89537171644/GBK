"""Simple non-neural baseline ML report for deterministic datasets."""

import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sp63_core.dataset import (
    DIAGNOSTIC_DATASET_SOURCE,
    DatasetCase,
    DiagnosticDatasetCase,
    split_diagnostic_dataset_by_group,
)

SAFE_REGRESSION_TARGETS: tuple[str, ...] = (
    "longitudinal_as_mm2",
    "bending_utilization",
)
DIAGNOSTIC_CLASSIFICATION_TARGET = "overall_status"
SAFE_REGRESSION_FEATURES: tuple[str, ...] = (
    "section_b_mm",
    "section_h_mm",
    "cover_mm",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
    "concrete_class_code",
    "main_rebar_class_code",
    "stirrup_rebar_class_code",
)
DIAGNOSTIC_CLASSIFICATION_FEATURES: tuple[str, ...] = (
    *SAFE_REGRESSION_FEATURES,
    "main_bar_count",
    "main_bar_diameter_mm",
    "stirrup_diameter_mm",
    "stirrup_legs",
    "stirrup_spacing_mm",
)
EXPANDED_DIAGNOSTIC_INPUT_FEATURES: tuple[str, ...] = (
    "section_b_mm",
    "section_h_mm",
    "effective_depth_mm",
    "cover_mm",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
    "concrete_class_code",
    "main_rebar_class_code",
    "stirrup_rebar_class_code",
    "main_bar_count",
    "main_bar_diameter_mm",
    "stirrup_diameter_mm",
    "stirrup_legs",
    "stirrup_spacing_mm",
    "longitudinal_as_mm2",
    "transverse_asw_mm2",
)
EXPANDED_DIAGNOSTIC_DETERMINISTIC_DERIVED_FEATURES: tuple[str, ...] = (
    *EXPANDED_DIAGNOSTIC_INPUT_FEATURES,
    "bending_mult_nmm",
    "shear_qult_n",
    "mcrc_nmm",
    "crack_width_mm",
    "deflection_mm",
)
EXPANDED_DIAGNOSTIC_SMALL_DATASET_LIMIT = 1000
BASELINE_REPORT_NOTES: tuple[str, ...] = (
    "ML is advisory-only and is not a deterministic design checker.",
    "Neural network is not used in this baseline report.",
    "Deterministic SP63 checks remain mandatory for every ML proposal.",
)


@dataclass(frozen=True)
class BaselineMLReport:
    """Metrics for simple non-neural ML smoke baselines."""

    status: str
    safe_rows: int
    diagnostic_rows: int
    regression_targets: tuple[str, ...]
    classification_target: str
    regression_feature_columns: tuple[str, ...]
    classification_feature_columns: tuple[str, ...]
    regression_models: dict[str, str]
    classification_models: dict[str, str]
    regression_metrics: dict[str, dict[str, float]]
    classification_metrics: dict[str, Any]
    expanded_diagnostic_classification: dict[str, Any]
    diagnostic_status_counts: dict[str, int]
    warnings: tuple[str, ...]
    notes: tuple[str, ...]
    ml_is_advisory_only: bool = True
    neural_network_used: bool = False
    deterministic_checks_required: bool = True
    requires_engineer_review: bool = True


def build_baseline_ml_report(
    safe_cases: Sequence[DatasetCase],
    diagnostic_cases: Sequence[DiagnosticDatasetCase],
    *,
    seed: int = 42,
) -> BaselineMLReport:
    """Build non-neural baseline metrics for safe and diagnostic datasets."""
    if not safe_cases:
        raise ValueError("safe_cases must not be empty")
    if not diagnostic_cases:
        raise ValueError("diagnostic_cases must not be empty")

    regression_metrics = _build_regression_metrics(safe_cases, seed=seed)
    classification_metrics = _build_classification_metrics(diagnostic_cases)
    expanded_diagnostic_classification = _build_expanded_diagnostic_classification(
        diagnostic_cases,
        seed=seed,
    )
    diagnostic_status_counts = dict(
        sorted(Counter(case.overall_status for case in diagnostic_cases).items())
    )

    warnings: list[str] = []
    if len(diagnostic_cases) < 30:
        warnings.append(
            "diagnostic dataset is small; classification metrics are smoke metrics only"
        )
    if len(diagnostic_status_counts) < 2:
        warnings.append(
            "diagnostic dataset has fewer than two overall_status classes; "
            "classification baseline is not meaningful"
        )
    if "pass" not in diagnostic_status_counts or "fail" not in diagnostic_status_counts:
        warnings.append(
            "diagnostic dataset should include both pass and fail rows before ML review"
        )
    warnings.extend(expanded_diagnostic_classification["warnings"])

    if expanded_diagnostic_classification["status"] == "fail":
        status = "fail"
    else:
        status = "review_required" if warnings else "pass"
    return BaselineMLReport(
        status=status,
        safe_rows=len(safe_cases),
        diagnostic_rows=len(diagnostic_cases),
        regression_targets=SAFE_REGRESSION_TARGETS,
        classification_target=DIAGNOSTIC_CLASSIFICATION_TARGET,
        regression_feature_columns=SAFE_REGRESSION_FEATURES,
        classification_feature_columns=DIAGNOSTIC_CLASSIFICATION_FEATURES,
        regression_models={
            "dummy": "DummyRegressor(strategy='mean')",
            "ridge": "Ridge",
        },
        classification_models={
            "dummy": "DummyClassifier(strategy='most_frequent')",
            "logistic": "LogisticRegression",
        },
        regression_metrics=regression_metrics,
        classification_metrics=classification_metrics,
        expanded_diagnostic_classification=expanded_diagnostic_classification,
        diagnostic_status_counts=diagnostic_status_counts,
        warnings=tuple(warnings),
        notes=BASELINE_REPORT_NOTES,
    )


def _build_regression_metrics(
    safe_cases: Sequence[DatasetCase],
    *,
    seed: int,
) -> dict[str, dict[str, float]]:
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    train_cases, test_cases = _train_test_split(tuple(safe_cases), seed=seed)
    train_features = [_safe_regression_features(case) for case in train_cases]
    test_features = [_safe_regression_features(case) for case in test_cases]

    metrics: dict[str, dict[str, float]] = {}
    for target_name in SAFE_REGRESSION_TARGETS:
        train_target = [_safe_target(case, target_name) for case in train_cases]
        test_target = [_safe_target(case, target_name) for case in test_cases]

        dummy = DummyRegressor(strategy="mean")
        dummy.fit(train_features, train_target)
        dummy_predictions = dummy.predict(test_features)

        ridge = make_pipeline(StandardScaler(), Ridge())
        ridge.fit(train_features, train_target)
        ridge_predictions = ridge.predict(test_features)

        metrics[target_name] = {
            "dummy_mae": float(mean_absolute_error(test_target, dummy_predictions)),
            "ridge_mae": float(mean_absolute_error(test_target, ridge_predictions)),
            "ridge_mape_percent": float(
                mean_absolute_percentage_error(test_target, ridge_predictions) * 100.0
            ),
            "train_rows": float(len(train_cases)),
            "test_rows": float(len(test_cases)),
        }
    return metrics


def _build_classification_metrics(
    diagnostic_cases: Sequence[DiagnosticDatasetCase],
) -> dict[str, Any]:
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    features = [_diagnostic_classification_features(case) for case in diagnostic_cases]
    target = [case.overall_status for case in diagnostic_cases]
    classes = tuple(sorted(set(target)))

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(features, target)
    dummy_predictions = dummy.predict(features)

    logistic_accuracy: float | None
    if len(classes) >= 2:
        logistic = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        )
        logistic.fit(features, target)
        logistic_predictions = logistic.predict(features)
        logistic_accuracy = float(accuracy_score(target, logistic_predictions))
    else:
        logistic_accuracy = None

    return {
        "target": DIAGNOSTIC_CLASSIFICATION_TARGET,
        "dummy_accuracy": float(accuracy_score(target, dummy_predictions)),
        "logistic_accuracy": logistic_accuracy,
        "row_count": float(len(diagnostic_cases)),
        "class_count": float(len(classes)),
        "classes": classes,
        "dataset_source": DIAGNOSTIC_DATASET_SOURCE,
    }


def _build_expanded_diagnostic_classification(
    diagnostic_cases: Sequence[DiagnosticDatasetCase],
    *,
    seed: int,
) -> dict[str, Any]:
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    target = [case.overall_status for case in diagnostic_cases]
    labels = tuple(sorted(set(target)))
    class_distribution = dict(sorted(Counter(target).items()))

    warnings: list[str] = []
    group_key_present = all(
        getattr(case, "group_key", "") not in (None, "") for case in diagnostic_cases
    )
    if len(diagnostic_cases) < EXPANDED_DIAGNOSTIC_SMALL_DATASET_LIMIT:
        warnings.append(
            "expanded diagnostic dataset has fewer than 1000 rows; "
            "classification metrics are review-only"
        )
    if not group_key_present:
        warnings.append("diagnostic dataset has no group_key; group leakage cannot be checked")
    warnings.append(
        "deterministic_derived_features include deterministic output values and may "
        "leak target information for project ML"
    )

    if len(labels) < 2:
        return {
            "status": "fail",
            "target": DIAGNOSTIC_CLASSIFICATION_TARGET,
            "target_constant": True,
            "class_distribution": class_distribution,
            "train_rows": 0,
            "test_rows": 0,
            "split": {
                "random_state": seed,
                "group_key_present": group_key_present,
                "group_leakage_checked": group_key_present,
                "group_leakage_count": 0,
            },
            "feature_modes": {},
            "warnings": tuple(
                [
                    "expanded diagnostic classification target is constant; "
                    "baseline cannot be evaluated"
                ]
                + warnings
            ),
        }

    group_split = None
    if group_key_present:
        group_split = split_diagnostic_dataset_by_group(diagnostic_cases, seed=seed)
        train_cases = group_split.train
        test_cases = group_split.test
        if not train_cases or not test_cases:
            train_cases, test_cases = _stratified_diagnostic_split(
                tuple(diagnostic_cases),
                seed=seed,
            )
    else:
        train_cases, test_cases = _stratified_diagnostic_split(
            tuple(diagnostic_cases),
            seed=seed,
        )
    feature_modes = {
        "input_only_features": _evaluate_classification_feature_mode(
            train_cases=train_cases,
            test_cases=test_cases,
            feature_columns=EXPANDED_DIAGNOSTIC_INPUT_FEATURES,
            labels=labels,
            deterministic_derived=False,
            dummy_classifier=DummyClassifier(strategy="most_frequent"),
            logistic_classifier=make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ),
        "deterministic_derived_features": _evaluate_classification_feature_mode(
            train_cases=train_cases,
            test_cases=test_cases,
            feature_columns=EXPANDED_DIAGNOSTIC_DETERMINISTIC_DERIVED_FEATURES,
            labels=labels,
            deterministic_derived=True,
            dummy_classifier=DummyClassifier(strategy="most_frequent"),
            logistic_classifier=make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ),
    }
    return {
        "status": "review_required" if warnings else "pass",
        "target": DIAGNOSTIC_CLASSIFICATION_TARGET,
        "target_constant": False,
        "class_distribution": class_distribution,
        "train_rows": len(train_cases),
        "test_rows": len(test_cases),
        "split": {
            "random_state": seed,
            "strategy": (
                "group_shuffle_by_group_key"
                if group_key_present
                else "stratified_by_overall_status"
            ),
            "group_key_present": group_key_present,
            "group_leakage_checked": group_key_present,
            "group_leakage_count": (
                0 if group_split is None else group_split.group_leakage_count
            ),
            "train_group_count": 0 if group_split is None else group_split.train_group_count,
            "test_group_count": 0 if group_split is None else group_split.test_group_count,
        },
        "feature_modes": feature_modes,
        "warnings": tuple(warnings),
    }


def _evaluate_classification_feature_mode(
    *,
    train_cases: tuple[DiagnosticDatasetCase, ...],
    test_cases: tuple[DiagnosticDatasetCase, ...],
    feature_columns: tuple[str, ...],
    labels: tuple[str, ...],
    deterministic_derived: bool,
    dummy_classifier: Any,
    logistic_classifier: Any,
) -> dict[str, Any]:
    train_features = [
        _expanded_diagnostic_features(case, feature_columns) for case in train_cases
    ]
    test_features = [
        _expanded_diagnostic_features(case, feature_columns) for case in test_cases
    ]
    train_target = [case.overall_status for case in train_cases]
    test_target = [case.overall_status for case in test_cases]

    dummy_classifier.fit(train_features, train_target)
    logistic_classifier.fit(train_features, train_target)

    return {
        "feature_columns": feature_columns,
        "deterministic_derived_features_used": deterministic_derived,
        "models": {
            "dummy": "DummyClassifier(strategy='most_frequent')",
            "logistic": "LogisticRegression",
        },
        "dummy": _classification_metrics(
            true_values=test_target,
            predicted_values=dummy_classifier.predict(test_features),
            labels=labels,
        ),
        "logistic": _classification_metrics(
            true_values=test_target,
            predicted_values=logistic_classifier.predict(test_features),
            labels=labels,
        ),
    }


def _classification_metrics(
    *,
    true_values: list[str],
    predicted_values: Any,
    labels: tuple[str, ...],
) -> dict[str, Any]:
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )

    return {
        "accuracy": float(accuracy_score(true_values, predicted_values)),
        "macro_f1": float(
            f1_score(true_values, predicted_values, labels=labels, average="macro")
        ),
        "per_class_precision": dict(
            zip(
                labels,
                (
                    float(value)
                    for value in precision_score(
                        true_values,
                        predicted_values,
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
                        true_values,
                        predicted_values,
                        labels=labels,
                        average=None,
                        zero_division=0,
                    )
                ),
                strict=True,
            )
        ),
        "confusion_matrix": confusion_matrix(
            true_values,
            predicted_values,
            labels=labels,
        ).tolist(),
        "labels": labels,
    }


def _stratified_diagnostic_split(
    cases: tuple[DiagnosticDatasetCase, ...],
    *,
    seed: int,
) -> tuple[tuple[DiagnosticDatasetCase, ...], tuple[DiagnosticDatasetCase, ...]]:
    rng = random.Random(seed)
    by_status: dict[str, list[DiagnosticDatasetCase]] = {}
    for case in cases:
        by_status.setdefault(case.overall_status, []).append(case)

    train_cases: list[DiagnosticDatasetCase] = []
    test_cases: list[DiagnosticDatasetCase] = []
    for status_cases in by_status.values():
        shuffled = list(status_cases)
        rng.shuffle(shuffled)
        if len(shuffled) == 1:
            train_cases.extend(shuffled)
            continue
        test_count = max(1, int(round(len(shuffled) * 0.3)))
        if test_count >= len(shuffled):
            test_count = len(shuffled) - 1
        test_cases.extend(shuffled[:test_count])
        train_cases.extend(shuffled[test_count:])

    rng.shuffle(train_cases)
    rng.shuffle(test_cases)
    if not test_cases:
        test_cases = train_cases[:1]
    return tuple(train_cases), tuple(test_cases)


def _train_test_split(
    cases: tuple[DatasetCase, ...],
    *,
    seed: int,
) -> tuple[tuple[DatasetCase, ...], tuple[DatasetCase, ...]]:
    if len(cases) < 2:
        return cases, cases
    shuffled = list(cases)
    random.Random(seed).shuffle(shuffled)
    train_count = max(1, int(len(shuffled) * 0.7))
    if train_count >= len(shuffled):
        train_count = len(shuffled) - 1
    return tuple(shuffled[:train_count]), tuple(shuffled[train_count:])


def _safe_regression_features(case: DatasetCase) -> list[float]:
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


def _diagnostic_classification_features(case: DiagnosticDatasetCase) -> list[float]:
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
        float(case.main_bar_count),
        float(case.main_bar_diameter_mm),
        float(case.stirrup_diameter_mm),
        float(case.stirrup_legs),
        float(case.stirrup_spacing_mm),
    ]


def _expanded_diagnostic_features(
    case: DiagnosticDatasetCase,
    feature_columns: tuple[str, ...],
) -> list[float]:
    return [_expanded_feature_value(case, feature_name) for feature_name in feature_columns]


def _expanded_feature_value(
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


def _safe_target(case: DatasetCase, target_name: str) -> float:
    if target_name == "longitudinal_as_mm2":
        return float(case.longitudinal_as_mm2)
    if target_name == "bending_utilization":
        return float(case.bending_utilization)
    raise ValueError(f"unsupported regression target {target_name!r}")


def _class_code(class_name: str) -> float:
    digits = "".join(character for character in class_name if character.isdigit())
    if not digits:
        raise ValueError(f"cannot derive numeric class code from {class_name!r}")
    return float(digits)
