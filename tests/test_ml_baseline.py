from sp63_core.dataset import generate_dataset_cases, split_dataset_cases
from sp63_core.ml import (
    evaluate_baseline_models,
    evaluate_ml_safety,
    load_baseline_model_bundle,
    save_baseline_model_bundle,
    train_baseline_models,
)


def test_train_evaluate_save_and_load_baseline_models(tmp_path):
    cases = generate_dataset_cases(limit=50)
    split = split_dataset_cases(cases, group_by="group_key")

    bundle = train_baseline_models(split.train)
    metrics = evaluate_baseline_models(bundle, split.test)
    safety_metrics = evaluate_ml_safety(bundle, split.test)
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
    assert "stirrup_diameter_accuracy" not in metrics
    assert "stirrup_legs_accuracy" in metrics
    assert "stirrup_spacing_accuracy" in metrics
    assert "target_count" in metrics
    assert "feature_count" in metrics
    assert "unsafe_prediction_rate" in safety_metrics
    assert "deterministic_accept_rate" in safety_metrics
    assert bundle.metadata["stirrup_diameter_mode"] == "input_geometry_parameter"
    assert bundle.metadata["target_leakage_checked"] is True
