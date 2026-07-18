"""Tests for deterministic verification of advisory ML proposals."""

import json

import pytest

from sp63_core.cli import main
from sp63_core.ml import MLProposal, verify_ml_proposal_with_deterministic_core


def test_diagnostic_pass_proposal_is_blocked_while_ed01_is_open():
    proposal = MLProposal(
        proposal_id="pass",
        proposal_type="rectangular_rebar_scheme",
        input_data=_base_input(),
        proposed_values={
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.verification_status == "rejected"
    assert result.deterministic_strength_status == "outside_applicability"
    assert result.deterministic_serviceability_status == "pass"
    assert result.deterministic_overall_status == "outside_applicability"
    assert result.layout_feasible is True
    assert result.longitudinal_constructive_status == "pass"
    assert result.transverse_constructive_status in ("pass", "warning")
    assert result.completeness_status == "incomplete"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use_status == "prohibited"
    assert result.project_use is False
    assert result.requires_engineer_review is True
    assert "ML proposal is advisory-only" in result.warnings
    assert "deterministic SP63 verification is mandatory" in result.warnings
    assert "bending check is outside applicability" in result.rejection_reasons


def test_bending_fail_proposal_is_rejected():
    proposal = MLProposal(
        proposal_id="bending_fail",
        proposal_type="rectangular_rebar_scheme",
        input_data=_base_input(),
        proposed_values={
            "main_bar_count": 2,
            "main_bar_diameter": 12,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.deterministic_strength_status == "outside_applicability"
    assert "bending check is outside applicability" in result.rejection_reasons
    assert "ML proposal rejected by deterministic SP63 verification" in result.warnings


def test_shear_fail_proposal_is_rejected():
    input_data = _base_input()
    input_data.update({"M": 10_000_000, "Q": 250_000, "Mser": None, "span": None})
    proposal = MLProposal(
        proposal_id="shear_fail",
        proposal_type="rectangular_rebar_scheme",
        input_data=input_data,
        proposed_values={
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 6,
            "stirrup_legs": 2,
            "stirrup_spacing": 300,
        },
        model_name="test_model",
        model_kind="baseline_ml",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.deterministic_strength_status == "outside_applicability"
    assert result.deterministic_serviceability_status == "not_checked"
    assert "bending check is outside applicability" in result.rejection_reasons
    assert "shear check failed" in result.rejection_reasons


def test_physically_infeasible_single_layer_proposal_is_rejected():
    proposal = MLProposal(
        proposal_id="layout_fail",
        proposal_type="rectangular_rebar_scheme",
        input_data=_base_input(),
        proposed_values={
            "main_bar_count": 8,
            "main_bar_diameter": 16,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.layout_feasible is False
    assert "single-layer longitudinal layout is not feasible" in result.rejection_reasons
    assert result.project_use is False


def test_serviceability_fail_proposal_is_rejected():
    input_data = _base_input()
    input_data.update({"M": 10_000_000, "Q": 0, "Mser": 90_000_000, "span": 12_000})
    proposal = MLProposal(
        proposal_id="serviceability_fail",
        proposal_type="rectangular_rebar_scheme",
        input_data=input_data,
        proposed_values={
            "main_bar_count": 2,
            "main_bar_diameter": 16,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.deterministic_strength_status == "outside_applicability"
    assert result.deterministic_serviceability_status == "fail"
    assert result.deterministic_overall_status == "fail"
    assert "crack_width check failed" in result.rejection_reasons
    assert "deflection check failed" in result.rejection_reasons


def test_long_duration_proposal_is_rejected_before_deterministic_checks():
    input_data = _base_input()
    input_data["load_duration"] = "long"
    proposal = MLProposal(
        proposal_id="long_duration",
        proposal_type="rectangular_rebar_scheme",
        input_data=input_data,
        proposed_values={
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    result = verify_ml_proposal_with_deterministic_core(proposal)

    assert result.accepted is False
    assert result.deterministic_strength_status == "not_checked"
    assert result.deterministic_serviceability_status == "not_checked"
    assert result.completeness_status == "incomplete"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use_status == "prohibited"
    assert result.project_use is False
    assert any("shear load-combination context" in item for item in result.rejection_reasons)


def test_missing_orientation_is_not_fabricated_for_ml_proposal():
    input_data = _base_input()
    input_data.pop("local_axes_id")
    proposal = MLProposal(
        proposal_id="missing_orientation",
        proposal_type="rectangular_rebar_scheme",
        input_data=input_data,
        proposed_values={
            "main_bar_count": 3,
            "main_bar_diameter": 20,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    with pytest.raises(ValueError, match="local_axes_id"):
        verify_ml_proposal_with_deterministic_core(proposal)


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf")])
def test_nonfinite_ml_proposal_values_are_rejected(invalid_value):
    proposal = MLProposal(
        proposal_id="nonfinite",
        proposal_type="rectangular_rebar_scheme",
        input_data=_base_input(),
        proposed_values={
            "main_bar_count": 3,
            "main_bar_diameter": invalid_value,
            "stirrup_diameter": 8,
            "stirrup_legs": 2,
            "stirrup_spacing": 200,
        },
        model_name="test_model",
        model_kind="neural_surrogate",
    )

    with pytest.raises(ValueError, match="finite and positive"):
        verify_ml_proposal_with_deterministic_core(proposal)


def test_cli_ml_proposal_verify_json_output(capsys):
    exit_code = main(["ml-proposal-verify", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-proposal-verify"
    assert data["status"] == "review_required"
    assert data["verified_count"] == 2
    assert data["accepted_count"] == 0
    assert data["rejected_count"] == 2
    assert data["ml_is_advisory_only"] is True
    assert data["deterministic_checks_required"] is True
    assert data["completeness_status"] == "incomplete"
    assert data["evidence_status"] == "needs_engineer_review"
    assert data["project_use_status"] == "prohibited"
    assert data["project_use"] is False
    assert all(not result["accepted"] for result in data["results"])


def _base_input() -> dict[str, object]:
    return {
        "b": 300,
        "h": 500,
        "cover": 32,
        "stirrup_diameter_for_geometry": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "M": 150_000_000,
        "Q": 80_000,
        "local_axes_id": "ml-proposal-test-local-axes",
        "moment_axis": "local_z",
        "tension_face": "local_y_min",
        "load_duration": "short",
        "Mser": 30_000_000,
        "span": 6000,
    }
