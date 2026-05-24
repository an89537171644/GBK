"""Tests for deterministic verification of advisory ML proposals."""

import json

from sp63_core.cli import main
from sp63_core.ml import MLProposal, verify_ml_proposal_with_deterministic_core


def test_pass_proposal_is_accepted():
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

    assert result.accepted is True
    assert result.verification_status == "accepted"
    assert result.deterministic_strength_status == "pass"
    assert result.deterministic_serviceability_status == "pass"
    assert result.deterministic_overall_status == "pass"
    assert result.requires_engineer_review is True
    assert "ML proposal is advisory-only" in result.warnings
    assert "deterministic SP63 verification is mandatory" in result.warnings


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
    assert result.deterministic_strength_status == "fail"
    assert "bending check failed" in result.rejection_reasons
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
    assert result.deterministic_strength_status == "fail"
    assert result.deterministic_serviceability_status == "not_checked"
    assert "shear check failed" in result.rejection_reasons


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
    assert result.deterministic_strength_status == "pass"
    assert result.deterministic_serviceability_status == "fail"
    assert result.deterministic_overall_status == "fail"
    assert "crack_width check failed" in result.rejection_reasons
    assert "deflection check failed" in result.rejection_reasons


def test_cli_ml_proposal_verify_json_output(capsys):
    exit_code = main(["ml-proposal-verify", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-proposal-verify"
    assert data["status"] == "pass"
    assert data["verified_count"] == 2
    assert data["accepted_count"] == 1
    assert data["rejected_count"] == 1
    assert data["ml_is_advisory_only"] is True
    assert data["deterministic_checks_required"] is True
    assert any(result["accepted"] for result in data["results"])
    assert any(not result["accepted"] for result in data["results"])


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
        "Mser": 30_000_000,
        "span": 6000,
    }
