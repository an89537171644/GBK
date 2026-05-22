from sp63_core.dataset import export_dataset_csv, generate_dataset_cases
from sp63_core.ml import train_neural_as_model


def test_train_neural_model_saves_metrics_and_model(tmp_path):
    cases = generate_dataset_cases(limit=30)
    csv_path = export_dataset_csv(cases, tmp_path / "train.csv")
    model_path = tmp_path / "neural.joblib"

    result = train_neural_as_model(csv_path, model_path=model_path)

    assert result.train_rows > 0
    assert result.mae >= 0
    assert result.mape >= 0
    assert result.model_path == str(model_path)
    assert result.requires_deterministic_check is True
    assert model_path.exists()
