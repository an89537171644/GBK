from sp63_core.dataset import generate_dataset_cases
from sp63_core.ml import check_ml_prediction_safety


def test_check_ml_prediction_safety_is_advisory_and_uses_deterministic_core():
    case = generate_dataset_cases(limit=1)[0]
    prediction = {
        "As_provided": case.As_provided,
        "main_bar_diameter": case.main_bar_diameter,
        "stirrup_spacing": case.stirrup_spacing,
    }

    safety = check_ml_prediction_safety(prediction, case)

    assert safety["ml_is_advisory"] is True
    assert safety["accepted_by_deterministic_core"] is True
    assert safety["deterministic_status"] == "pass"
    assert safety["warnings"]
