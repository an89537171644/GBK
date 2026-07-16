from sp63_core.dataset import generate_dataset_cases
from sp63_core.ml import (
    MLReinforcementProposal,
    check_ml_prediction_safety,
    check_ml_proposal_safety,
)


def test_check_ml_proposal_safety_accepts_case_reinforcement():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
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
    assert safety["local_axes_id"] == case.local_axes_id
    assert safety["moment_axis"] == case.moment_axis
    assert safety["tension_face"] == case.tension_face
    assert safety["completeness_status"] == "incomplete"
    assert safety["evidence_status"] == "needs_engineer_review"
    assert safety["project_use_status"] == "prohibited"
    assert safety["project_use"] is False
    assert safety["requires_engineer_review"] is True
    assert safety["warnings"]


def test_check_ml_proposal_safety_rejects_bad_reinforcement():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
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
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
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


def test_check_ml_proposal_safety_always_rejects_long_duration():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]
    object.__setattr__(case, "load_duration", "long")
    proposal = MLReinforcementProposal(
        main_bar_count=case.main_bar_count,
        main_bar_diameter=case.main_bar_diameter,
        stirrup_diameter=case.stirrup_diameter,
        stirrup_legs=case.stirrup_legs,
        stirrup_spacing=case.stirrup_spacing,
    )

    safety = check_ml_proposal_safety(proposal, case)

    assert safety["accepted_by_deterministic_core"] is False
    assert safety["bending_status"] == "not_checked"
    assert safety["shear_status"] == "not_checked"
    assert safety["load_duration"] == "long"
    assert safety["completeness_status"] == "incomplete"
    assert safety["evidence_status"] == "needs_engineer_review"
    assert safety["project_use_status"] == "prohibited"
    assert safety["project_use"] is False
    assert safety["requires_engineer_review"] is True
    assert any("shear load-combination context" in item for item in safety["warnings"])
