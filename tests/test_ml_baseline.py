from sp63_core.dataset import generate_dataset_cases, split_dataset_cases
from sp63_core.ml import (
    evaluate_baseline_models,
    load_baseline_model_bundle,
    save_baseline_model_bundle,
    train_baseline_models,
)


def test_train_evaluate_save_and_load_baseline_models(tmp_path):
    cases = generate_dataset_cases(limit=50)
    split = split_dataset_cases(cases, group_by="group_key")

    bundle = train_baseline_models(split.train)
    metrics = evaluate_baseline_models(bundle, split.test)
    model_path = save_baseline_model_bundle(bundle, tmp_path / "baseline_model.pkl")
    loaded = load_baseline_model_bundle(model_path)

    assert model_path.exists()
    assert loaded.requires_deterministic_check is True
    assert loaded.feature_columns == bundle.feature_columns
    assert "As_MAE" in metrics
    assert "As_MAPE" in metrics
    assert "bending_utilization_MAE" in metrics
    assert "shear_utilization_MAE" in metrics
    assert "main_bar_diameter_accuracy" in metrics
    assert "main_bar_count_accuracy" in metrics
    assert "stirrup_diameter_accuracy" in metrics
    assert "stirrup_spacing_accuracy" in metrics
