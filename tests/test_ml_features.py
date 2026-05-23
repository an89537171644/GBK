from sp63_core.dataset import generate_dataset_cases
from sp63_core.ml import build_feature_matrix


def test_build_feature_matrix_returns_features_and_targets():
    cases = generate_dataset_cases(limit=5)

    features, targets = build_feature_matrix(cases)

    assert features
    assert targets
    assert len(features) == len(cases)
    assert len(targets) == len(cases)
    assert "b" in features[0]
    assert "cover" in features[0]
    assert "As_provided" in targets[0]


def test_build_feature_matrix_does_not_leak_targets_to_features():
    cases = generate_dataset_cases(limit=5)

    features, _ = build_feature_matrix(cases)

    assert "As_provided" not in features[0]
    assert "status" not in features[0]
    assert "main_rebar_scheme" not in features[0]
    assert "stirrup_scheme" not in features[0]
    assert "main_bar_diameter" not in features[0]
    assert "main_bar_count" not in features[0]
    assert "h0" not in features[0]
    assert "stirrup_spacing" not in features[0]
    assert "stirrup_diameter" not in features[0]
    assert "stirrup_legs" not in features[0]
    assert "bending_utilization" not in features[0]
    assert "shear_utilization" not in features[0]


def test_build_feature_matrix_uses_cover_and_geometry_stirrup_as_inputs():
    cases = generate_dataset_cases(limit=5)

    features, _ = build_feature_matrix(cases)

    assert "cover" in features[0]
    assert "geometry_stirrup_diameter" in features[0]


def test_stirrup_diameter_is_not_target():
    cases = generate_dataset_cases(limit=5)

    _, targets = build_feature_matrix(cases)

    assert "stirrup_diameter" not in targets[0]
