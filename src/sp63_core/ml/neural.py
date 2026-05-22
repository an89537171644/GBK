"""Neural surrogate model for predicting As_required.

The surrogate is only an assistant. Any reinforcement option suggested from
its prediction must still pass the deterministic calculation core.
"""

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sp63_core.ml.baseline import mean_absolute_percentage_error_safe
from sp63_core.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    split_features_target,
    validate_training_dataframe,
)


@dataclass(frozen=True)
class NeuralTrainingResult:
    """Training metrics for the draft neural As_required surrogate."""

    train_rows: int
    mae: float
    mape: float
    model_path: str | None
    requires_deterministic_check: bool = True


def train_neural_as_model(
    train_csv: str | Path,
    model_path: str | Path | None = None,
    random_state: int = 42,
) -> NeuralTrainingResult:
    """Train and optionally persist the neural As_required surrogate."""
    df = pd.read_csv(train_csv)
    validate_training_dataframe(df)
    X, y = split_features_target(df)

    model = _build_pipeline(random_state=random_state)
    model.fit(X, y)
    predictions = model.predict(X)

    saved_path: str | None = None
    if model_path is not None:
        output_path = Path(model_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, output_path)
        saved_path = str(output_path)

    return NeuralTrainingResult(
        train_rows=len(df),
        mae=float(np.mean(np.abs(y.to_numpy(dtype=float) - predictions))),
        mape=mean_absolute_percentage_error_safe(y, predictions),
        model_path=saved_path,
        requires_deterministic_check=True,
    )


def _build_pipeline(*, random_state: int) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), list(CATEGORICAL_FEATURES)),
        ]
    )
    regressor = MLPRegressor(
        hidden_layer_sizes=(32, 16),
        max_iter=500,
        random_state=random_state,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", regressor),
        ]
    )
