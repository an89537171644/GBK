from sp63_core.dataset import generate_dataset_cases
from sp63_core.ml import (
    MLReinforcementProposal,
    check_ml_prediction_safety,
    check_ml_proposal_safety,
)


def test_check_ml_proposal_safety_accepts_case_reinforcement():
    case = generate_dataset_cases(limit=1)[0]
    proposal = MLReinforcementProposal(
        main_bar_count=case.main_bar_count,
        main_bar_diameter=case.main_bar_diameter,
        stirrup_diameter=case.stirrup_diameter,
        stirrup_legs=case.stirrup_legs,
        stirrup_spacing=case.stirrup_spacing,
    )

    safety = check_ml_proposal_safety(proposal, case)

    assert safety["ml_is_advisory"] is True
    assert safety["accepted_by_deterministic_core"] is True
    assert safety["bending_status"] == "pass"
    assert safety["shear_status"] == "pass"
    assert safety["stirrup_diameter_mode"] == "geometry_input_parameter"
    assert safety["warnings"]


def test_check_ml_proposal_safety_rejects_bad_reinforcement():
    case = generate_dataset_cases(limit=1)[0]
    proposal = MLReinforcementProposal(
        main_bar_count=1,
        main_bar_diameter=10,
        stirrup_diameter=6,
        stirrup_legs=2,
        stirrup_spacing=300,
    )

    safety = check_ml_proposal_safety(proposal, case)

    assert safety["ml_is_advisory"] is True
    assert safety["accepted_by_deterministic_core"] is False


def test_check_ml_prediction_safety_wraps_reconstructed_proposal():
    case = generate_dataset_cases(limit=1)[0]
    prediction = {
        "main_bar_count": case.main_bar_count,
        "main_bar_diameter": case.main_bar_diameter,
        "stirrup_legs": case.stirrup_legs,
        "stirrup_spacing": case.stirrup_spacing,
    }

    safety = check_ml_prediction_safety(prediction, case)

    assert safety["accepted_by_deterministic_core"] is True
    assert safety["proposal"]["stirrup_diameter"] == case.geometry_stirrup_diameter
    assert safety["proposal"]["requires_deterministic_check"] is True
