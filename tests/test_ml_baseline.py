import numpy as np
import pandas as pd
import pytest

from sp63_core.dataset import export_dataset_csv, generate_dataset_cases
from sp63_core.ml import (
    TARGET_AS,
    load_baseline_model,
    mean_absolute_percentage_error_safe,
    predict_as_required,
    split_features_target,
    train_baseline_as_model,
    validate_training_dataframe,
)


def test_train_baseline_model_saves_loads_and_predicts(tmp_path):
    cases = generate_dataset_cases(limit=20)
    csv_path = export_dataset_csv(cases, tmp_path / "train.csv")
    model_path = tmp_path / "baseline.joblib"

    result = train_baseline_as_model(csv_path, model_path=model_path)

    assert result.train_rows > 0
    assert result.mae >= 0
    assert result.mape >= 0
    assert result.model_path == str(model_path)
    assert result.requires_deterministic_check is True
    assert model_path.exists()

    model = load_baseline_model(model_path)
    df = pd.read_csv(csv_path)
    predictions = predict_as_required(model, df.head(3))

    assert isinstance(predictions, np.ndarray)
    assert len(predictions) == 3
    assert np.all(predictions > 0)


def test_split_features_target_returns_expected_columns(tmp_path):
    cases = generate_dataset_cases(limit=3)
    csv_path = export_dataset_csv(cases, tmp_path / "train.csv")
    df = pd.read_csv(csv_path)

    X, y = split_features_target(df)

    assert TARGET_AS not in X.columns
    assert len(X) == len(y) == 3
    assert y.name == TARGET_AS


def test_validate_training_dataframe_requires_target(tmp_path):
    cases = generate_dataset_cases(limit=3)
    csv_path = export_dataset_csv(cases, tmp_path / "train.csv")
    df = pd.read_csv(csv_path).drop(columns=[TARGET_AS])

    with pytest.raises(ValueError, match="missing required columns: As_required"):
        validate_training_dataframe(df)


def test_mean_absolute_percentage_error_safe_ignores_zero_true_values():
    value = mean_absolute_percentage_error_safe([0.0, 100.0, 200.0], [10.0, 90.0, 220.0])

    assert value == pytest.approx(0.1)


def test_predict_as_required_requires_feature_columns(tmp_path):
    cases = generate_dataset_cases(limit=20)
    csv_path = export_dataset_csv(cases, tmp_path / "train.csv")
    model_path = tmp_path / "baseline.joblib"
    train_baseline_as_model(csv_path, model_path=model_path)
    model = load_baseline_model(model_path)

    with pytest.raises(ValueError, match="missing required feature columns"):
        predict_as_required(model, pd.DataFrame({"b": [300.0]}))
