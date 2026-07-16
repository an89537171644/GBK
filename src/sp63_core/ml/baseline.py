"""Experimental baseline ML models for the beam-only strength dataset."""

import pickle
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core import __version__
from sp63_core.dataset import DATASET_VERSION, DatasetCase
from sp63_core.ml.features import FEATURE_COLUMNS, build_feature_matrix

REGRESSION_TARGETS: tuple[str, ...] = (
    "As_provided",
    "bending_utilization",
    "shear_utilization",
)
CLASSIFICATION_TARGETS: tuple[str, ...] = (
    "main_bar_diameter",
    "main_bar_count",
    "stirrup_legs",
    "stirrup_spacing",
)


@dataclass(frozen=True)
class BaselineModelBundle:
    """A saved group of experimental baseline models."""

    feature_columns: tuple[str, ...]
    models: dict[str, Any]
    metadata: dict[str, Any]
    requires_deterministic_check: bool = True
    dataset_version: str = DATASET_VERSION
    sp63_core_version: str = __version__


def train_baseline_models(
    train_cases: Sequence[DatasetCase],
    *,
    seed: int = 42,
) -> BaselineModelBundle:
    """Train simple RandomForest baselines on deterministic dataset rows."""
    if not train_cases:
        raise ValueError("train_cases must not be empty")
    if any(case.load_duration != "short" for case in train_cases):
        raise ValueError(
            "baseline training requires load_duration='short' until the "
            "shear load-combination context is implemented"
        )

    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    features, targets = build_feature_matrix(train_cases)
    feature_columns = FEATURE_COLUMNS
    matrix = _features_to_matrix(features, feature_columns)

    models: dict[str, Any] = {}
    for target_name in REGRESSION_TARGETS:
        model = RandomForestRegressor(
            n_estimators=30,
            random_state=seed,
            min_samples_leaf=1,
        )
        model.fit(matrix, [float(target[target_name]) for target in targets])
        models[target_name] = model

    for target_name in CLASSIFICATION_TARGETS:
        model = RandomForestClassifier(
            n_estimators=30,
            random_state=seed,
            min_samples_leaf=1,
        )
        model.fit(matrix, [target[target_name] for target in targets])
        models[target_name] = model

    return BaselineModelBundle(
        feature_columns=feature_columns,
        models=models,
        metadata={
            "model_family": "RandomForest",
            "train_rows": len(train_cases),
            "seed": seed,
            "stirrup_diameter_mode": "input_geometry_parameter",
            "target_leakage_checked": True,
            "h0_removed_from_features": True,
            "ml_is_advisory_only": True,
        },
    )


def predict_baseline_targets(
    model_bundle: BaselineModelBundle,
    cases: Sequence[DatasetCase],
) -> list[dict[str, float | int]]:
    """Predict all trained targets for dataset cases."""
    if not cases:
        raise ValueError("cases must not be empty")
    _validate_bundle_version(model_bundle)
    if any(case.load_duration != "short" for case in cases):
        raise ValueError(
            "baseline prediction requires load_duration='short' until the "
            "shear load-combination context is implemented"
        )

    features, _ = build_feature_matrix(cases)
    matrix = _features_to_matrix(features, model_bundle.feature_columns)
    predictions: list[dict[str, float | int]] = [dict() for _ in cases]
    for target_name, model in model_bundle.models.items():
        values = model.predict(matrix)
        for prediction, value in zip(predictions, values, strict=True):
            if target_name in CLASSIFICATION_TARGETS:
                prediction[target_name] = int(value)
            else:
                prediction[target_name] = float(value)
    return predictions


def save_baseline_model_bundle(bundle: BaselineModelBundle, path: str | Path) -> Path:
    """Serialize a baseline model bundle with pickle."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as output_file:
        pickle.dump(bundle, output_file)
    return output_path


def load_baseline_model_bundle(path: str | Path) -> BaselineModelBundle:
    """Load a baseline model bundle saved by save_baseline_model_bundle()."""
    with Path(path).open("rb") as input_file:
        loaded = pickle.load(input_file)
    if not isinstance(loaded, BaselineModelBundle):
        raise TypeError("pickle file does not contain a BaselineModelBundle")
    _validate_bundle_version(loaded)
    return loaded


def _validate_bundle_version(bundle: BaselineModelBundle) -> None:
    if bundle.dataset_version != DATASET_VERSION:
        raise ValueError(
            f"baseline model dataset_version {bundle.dataset_version!r} is incompatible; "
            f"expected {DATASET_VERSION!r}"
        )


def _features_to_matrix(
    features: Sequence[dict[str, float]],
    feature_columns: Sequence[str],
) -> list[list[float]]:
    return [[float(feature[column]) for column in feature_columns] for feature in features]
