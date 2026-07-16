from dataclasses import replace

import pytest

from sp63_core.dataset import (
    generate_dataset_cases,
    generate_diagnostic_dataset_cases,
    split_dataset_cases,
)
from sp63_core.ml import (
    build_baseline_ml_report,
    evaluate_baseline_models,
    evaluate_ml_safety,
    load_baseline_model_bundle,
    predict_baseline_targets,
    save_baseline_model_bundle,
    train_baseline_models,
)


def test_train_evaluate_save_and_load_baseline_models(tmp_path):
    cases = generate_dataset_cases(limit=50, load_duration="short")
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


def test_baseline_training_rejects_long_duration_rows():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
    object.__setattr__(case, "load_duration", "long")

    with pytest.raises(ValueError, match="baseline training requires load_duration='short'"):
        train_baseline_models((case,))


def test_baseline_model_bundle_rejects_legacy_dataset_version(tmp_path):
    cases = generate_dataset_cases(limit=5, load_duration="short")
    bundle = train_baseline_models(cases)
    legacy_bundle = replace(bundle, dataset_version="0.2")
    path = save_baseline_model_bundle(legacy_bundle, tmp_path / "legacy.pkl")

    with pytest.raises(ValueError, match="dataset_version '0.2' is incompatible"):
        load_baseline_model_bundle(path)
    with pytest.raises(ValueError, match="dataset_version '0.2' is incompatible"):
        predict_baseline_targets(legacy_bundle, cases)


def test_build_baseline_ml_report_uses_non_neural_models():
    safe_cases = generate_dataset_cases(limit=30, load_duration="short")
    diagnostic_cases = generate_diagnostic_dataset_cases(limit=1000)

    report = build_baseline_ml_report(safe_cases, diagnostic_cases)

    assert report.ml_is_advisory_only is True
    assert report.neural_network_used is False
    assert report.deterministic_checks_required is True
    assert report.requires_engineer_review is True
    assert "longitudinal_as_mm2" in report.regression_metrics
    assert "bending_utilization" in report.regression_metrics
    assert report.classification_metrics["target"] == "overall_status"
    assert report.diagnostic_status_counts["pass"] >= 1
    assert report.diagnostic_status_counts["fail"] >= 1
    assert report.diagnostic_status_counts["review_or_fail"] >= 1
    expanded = report.expanded_diagnostic_classification
    assert expanded["target"] == "overall_status"
    assert expanded["target_constant"] is False
    assert expanded["class_distribution"]["pass"] >= 1
    assert expanded["class_distribution"]["fail"] >= 1
    assert expanded["class_distribution"]["review_or_fail"] >= 1
    assert expanded["train_rows"] > 0
    assert expanded["test_rows"] > 0
    assert "input_only_features" in expanded["feature_modes"]
    assert "deterministic_derived_features" in expanded["feature_modes"]
    assert (
        expanded["feature_modes"]["input_only_features"][
            "deterministic_derived_features_used"
        ]
        is False
    )
    assert (
        expanded["feature_modes"]["deterministic_derived_features"][
            "deterministic_derived_features_used"
        ]
        is True
    )
    assert "overall_status" not in (
        expanded["feature_modes"]["input_only_features"]["feature_columns"]
    )
    assert (
        expanded["feature_modes"]["input_only_features"]["logistic"]["macro_f1"]
        >= 0.0
    )
    assert "neural" not in report.regression_models["ridge"].lower()
    assert expanded["split"]["group_key_present"] is True
    assert expanded["split"]["unique_group_count"] >= 50
    assert expanded["split"]["group_leakage_checked"] is True
    assert expanded["split"]["group_leakage_count"] == 0
    assert expanded["split"]["train_group_count"] > 1
    assert expanded["split"]["test_group_count"] > 1
    assert not any("fewer than 1000 rows" in warning for warning in report.warnings)
    assert not any("no group_key" in warning for warning in report.warnings)
    assert any(
        "deterministic_derived_features include deterministic output values" in warning
        for warning in report.warnings
    )
