"""Advisory neural prediction with mandatory deterministic verification."""

from __future__ import annotations

import warnings as py_warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import (
    build_report_dataset_feature_set,
    load_report_dataset_rows,
)
from sp63_core.design import design_rectangular_element
from sp63_core.ml.report_baseline import (
    _build_category_encoders,
    _feature_matrix,
    _split_rows,
)
from sp63_core.report import (
    build_rectangular_design_report,
    load_rectangular_design_input_from_json,
)

ADVISORY_PREDICTION_WARNINGS: tuple[str, ...] = (
    "neural advisory prediction is not a design checker",
    "deterministic SP63 verification is mandatory",
    "engineer review is required before any project use",
    "metrics and predictions are not production evidence",
)


@dataclass(frozen=True)
class NeuralAdvisoryPredictionResult:
    """One neural advisory prediction checked by deterministic SP63 output."""

    status: str
    source_dataset: str
    input_json_path: str
    target: str
    feature_mode: str
    predicted_status: str | None
    prediction_confidence: float | None
    class_probabilities: dict[str, float]
    deterministic_strength_status: str
    deterministic_serviceability_status: str
    deterministic_overall_status: str
    prediction_matches_deterministic: bool | None
    deterministic_report_required: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    requires_engineer_review: bool = True
    neural_network_used: bool = False
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    feature_columns: tuple[str, ...] = ()
    excluded_leakage_columns: tuple[str, ...] = ()


def build_neural_advisory_prediction(
    *,
    dataset_path: Path,
    input_json_path: Path,
    dataset_format: str | None = None,
    target: str = "overall_status",
    feature_mode: str = "input_only",
    hidden_layer_sizes: tuple[int, ...] = (16,),
    max_iter: int = 500,
    random_state: int = 42,
) -> NeuralAdvisoryPredictionResult:
    """Build one advisory ML prediction and verify it deterministically."""
    rows = load_report_dataset_rows(dataset_path, dataset_format)
    feature_set = build_report_dataset_feature_set(
        dataset_path=dataset_path,
        dataset_format=dataset_format,
        target=target,
        feature_mode=feature_mode,
        random_state=random_state,
    )
    warnings = [*feature_set.warnings, *ADVISORY_PREDICTION_WARNINGS]
    errors = list(feature_set.errors)
    if len(rows) < 100:
        warnings.append("dataset is too small for reliable advisory prediction")
    if feature_mode == "deterministic_derived":
        warnings.append(
            "deterministic-derived features may leak design decisions and must not be used "
            "for project ML decisions without review"
        )

    deterministic_report = _build_deterministic_report(input_json_path)
    deterministic_target_status = _deterministic_target_status(
        deterministic_report.json_data,
        target,
    )
    predicted_status: str | None = None
    prediction_confidence: float | None = None
    class_probabilities: dict[str, float] = {}
    prediction_matches_deterministic: bool | None = None
    neural_network_used = False

    if not errors and len(feature_set.target_distribution) >= 2:
        input_row = _build_input_feature_row(deterministic_report.json_data)
        (
            predicted_status,
            prediction_confidence,
            class_probabilities,
            model_used,
            model_warning,
        ) = _train_and_predict_status(
            rows=rows,
            input_row=input_row,
            feature_columns=feature_set.feature_columns,
            target=target,
            hidden_layer_sizes=hidden_layer_sizes,
            max_iter=max_iter,
            random_state=random_state,
        )
        neural_network_used = model_used
        if model_warning:
            warnings.append(model_warning)
        if predicted_status is not None and deterministic_target_status is not None:
            prediction_matches_deterministic = predicted_status == deterministic_target_status
            if not prediction_matches_deterministic:
                warnings.append(
                    "neural advisory prediction differs from deterministic SP63 result"
                )

    if errors:
        status = "fail"
    elif warnings:
        status = "review_required"
    else:
        status = "pass"

    return NeuralAdvisoryPredictionResult(
        status=status,
        source_dataset=str(dataset_path),
        input_json_path=str(input_json_path),
        target=target,
        feature_mode=feature_mode,
        predicted_status=predicted_status,
        prediction_confidence=prediction_confidence,
        class_probabilities=class_probabilities,
        deterministic_strength_status=deterministic_report.strength_status,
        deterministic_serviceability_status=deterministic_report.serviceability_status,
        deterministic_overall_status=deterministic_report.overall_status,
        prediction_matches_deterministic=prediction_matches_deterministic,
        deterministic_report_required=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        requires_engineer_review=True,
        neural_network_used=neural_network_used,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        feature_columns=feature_set.feature_columns,
        excluded_leakage_columns=feature_set.excluded_leakage_columns,
    )


def _build_deterministic_report(input_json_path: Path):
    design_input = load_rectangular_design_input_from_json(input_json_path)
    design_result = design_rectangular_element(design_input)
    return build_rectangular_design_report(design_result)


def _build_input_feature_row(report_data: dict[str, Any]) -> dict[str, Any]:
    input_data = _mapping(report_data.get("input_data"))
    geometry = _mapping(report_data.get("geometry"))
    reinforcement = _mapping(report_data.get("reinforcement"))
    longitudinal = _mapping(reinforcement.get("longitudinal"))
    transverse = _mapping(reinforcement.get("transverse"))
    return {
        "b": input_data.get("b"),
        "h": input_data.get("h"),
        "cover": input_data.get("cover"),
        "concrete_class": input_data.get("concrete_class"),
        "longitudinal_rebar_class": input_data.get("longitudinal_rebar_class"),
        "stirrup_rebar_class": input_data.get("stirrup_rebar_class"),
        "moment_axis": input_data.get("moment_axis"),
        "tension_face": input_data.get("tension_face"),
        "load_duration": input_data.get("load_duration"),
        "M": input_data.get("M"),
        "Q": input_data.get("Q"),
        "Mser": input_data.get("Mser"),
        "span": input_data.get("span"),
        "check_cracks": input_data.get("check_cracks"),
        "check_crack_width": input_data.get("check_crack_width"),
        "check_deflection": input_data.get("check_deflection"),
        "h0": geometry.get("h0"),
        "longitudinal_as_mm2": longitudinal.get("As"),
        "transverse_asw_mm2": transverse.get("Asw"),
        "main_bar_count": longitudinal.get("bar_count"),
        "main_bar_diameter": longitudinal.get("diameter"),
        "stirrup_diameter": transverse.get("diameter"),
        "stirrup_spacing": transverse.get("spacing"),
    }


def _deterministic_target_status(report_data: dict[str, Any], target: str) -> str | None:
    if target in {"strength_status", "serviceability_status", "overall_status"}:
        value = report_data.get(target)
        return None if value is None else str(value)
    checks = _mapping(report_data.get("checks"))
    check_name = target.removesuffix("_status")
    check = _mapping(checks.get(check_name))
    value = check.get("status")
    return None if value is None else str(value)


def _train_and_predict_status(
    *,
    rows: list[dict[str, Any]],
    input_row: dict[str, Any],
    feature_columns: tuple[str, ...],
    target: str,
    hidden_layer_sizes: tuple[int, ...],
    max_iter: int,
    random_state: int,
) -> tuple[str | None, float | None, dict[str, float], bool, str | None]:
    try:
        from sklearn.exceptions import ConvergenceWarning
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return (
            None,
            None,
            {},
            False,
            "scikit-learn is unavailable; neural advisory prediction was not trained",
        )

    train_rows, validation_rows, test_rows = _split_rows(rows, random_state=random_state)
    if not test_rows:
        test_rows = validation_rows or train_rows
    train_target = [str(row[target]) for row in train_rows]
    if len(set(train_target)) < 2:
        return (
            None,
            None,
            {},
            False,
            "training split has fewer than two target classes; "
            "neural advisory prediction was not trained",
        )

    encoders = _build_category_encoders([*train_rows, *test_rows, input_row], feature_columns)
    train_features = _feature_matrix(train_rows, feature_columns, encoders)
    input_features = _feature_matrix([input_row], feature_columns, encoders)
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
    predicted = str(classifier.predict(input_features)[0])
    probabilities = classifier.predict_proba(input_features)[0]
    classes = tuple(str(label) for label in classifier.classes_)
    class_probabilities = {
        class_name: float(probability)
        for class_name, probability in zip(classes, probabilities, strict=True)
    }
    prediction_confidence = max(class_probabilities.values()) if class_probabilities else None
    return predicted, prediction_confidence, class_probabilities, True, None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
