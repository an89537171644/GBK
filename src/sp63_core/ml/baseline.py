"""Baseline ML model for predicting As_required.

The model is only a predictor. Every reinforcement option proposed downstream
must still be checked by the deterministic calculation core.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from sp63_core.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    split_features_target,
    validate_training_dataframe,
)


@dataclass(frozen=True)
class BaselineTrainingResult:
    """Training metrics for the draft baseline As_required model."""

    train_rows: int
    mae: float
    mape: float
    model_path: str | None
    requires_deterministic_check: bool = True


def train_baseline_as_model(
    train_csv: str | Path,
    model_path: str | Path | None = None,
) -> BaselineTrainingResult:
    """Train and optionally persist the baseline As_required regressor."""
    df = pd.read_csv(train_csv)
    validate_training_dataframe(df)
    X, y = split_features_target(df)

    model = _build_pipeline()
    model.fit(X, y)
    predictions = model.predict(X)

    saved_path: str | None = None
    if model_path is not None:
        output_path = Path(model_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, output_path)
        saved_path = str(output_path)

    return BaselineTrainingResult(
        train_rows=len(df),
        mae=float(np.mean(np.abs(y.to_numpy(dtype=float) - predictions))),
        mape=mean_absolute_percentage_error_safe(y, predictions),
        model_path=saved_path,
        requires_deterministic_check=True,
    )


def load_baseline_model(model_path: str | Path) -> Any:
    """Load a persisted baseline model."""
    return joblib.load(model_path)


def predict_as_required(model: Any, input_rows: pd.DataFrame) -> np.ndarray:
    """Predict As_required for input rows."""
    missing = [
        column
        for column in (*NUMERIC_FEATURES, *CATEGORICAL_FEATURES)
        if column not in input_rows.columns
    ]
    if missing:
        raise ValueError(f"missing required feature columns: {', '.join(missing)}")
    return model.predict(input_rows[[*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]])


def mean_absolute_percentage_error_safe(y_true: Any, y_pred: Any) -> float:
    """Return MAPE while ignoring zero true values to avoid division by zero."""
    true = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    nonzero_mask = np.abs(true) > np.finfo(float).eps
    if not np.any(nonzero_mask):
        return 0.0
    return float(np.mean(np.abs((true[nonzero_mask] - pred[nonzero_mask]) / true[nonzero_mask])))


def _build_pipeline() -> Pipeline:
    encoder = OneHotEncoder(handle_unknown="ignore")
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", list(NUMERIC_FEATURES)),
            ("categorical", encoder, list(CATEGORICAL_FEATURES)),
        ]
    )
    regressor = RandomForestRegressor(
        n_estimators=50,
        random_state=42,
        min_samples_leaf=1,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )
