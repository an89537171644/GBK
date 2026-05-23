import pytest

from sp63_core.design import RectangularDesignInput, design_rectangular_element


def mvp_input(**overrides) -> RectangularDesignInput:
    data = {
        "b": 300,
        "h": 500,
        "cover": 32,
        "stirrup_diameter_for_geometry": 8,
        "concrete_class": "B25",
        "longitudinal_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "M": 150_000_000,
        "Q": 80_000,
        "load_duration": "short",
    }
    data.update(overrides)
    return RectangularDesignInput(**data)


def test_design_rectangular_element_returns_passing_result():
    result = design_rectangular_element(mvp_input())

    assert result.status == "pass"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.protocol is not None
    assert result.protocol.status == "pass"
    assert result.selected_longitudinal.bending.status == "pass"
    assert result.selected_longitudinal.constructive.status == "pass"
    assert result.selected_transverse.shear.status == "pass"
    assert result.selected_transverse.constructive.status in ("pass", "warning")
    assert result.selected_longitudinal.section.effective_depth() > 0
    assert result.selected_transverse.utilization <= 1.0


def test_design_rectangular_element_fails_when_no_longitudinal_option():
    result = design_rectangular_element(mvp_input(M=2_000_000_000))

    assert result.status == "fail"
    assert result.selected_longitudinal is None
    assert result.selected_transverse is None
    assert result.protocol is None
    assert "no passing longitudinal reinforcement options" in result.warnings


def test_design_rectangular_element_fails_when_no_transverse_option():
    result = design_rectangular_element(mvp_input(M=150_000_000, Q=2_000_000))

    assert result.status == "fail"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is None
    assert result.protocol is None
    assert "no passing transverse reinforcement options" in result.warnings


def test_design_rectangular_protocol_contains_selected_reinforcement():
    result = design_rectangular_element(mvp_input())

    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.protocol is not None
    assert result.protocol.reinforcement["main"] == result.selected_longitudinal.scheme
    assert result.protocol.reinforcement["stirrups"] == result.selected_transverse.scheme
    assert result.protocol.reinforcement["longitudinal_constructive_status"] == "pass"
    assert "longitudinal_reinforcement_ratio_percent" in result.protocol.reinforcement
    assert result.protocol.reinforcement["stirrup_constructive_status"] == "pass"
    assert "stirrup_constructive_max_spacing" in result.protocol.reinforcement
    assert "stirrup_sw_max_by_shear_rule" in result.protocol.reinforcement
    assert "stirrup_qsw_rule_status" in result.protocol.reinforcement
    assert "stirrup_transverse_reinforcement_countable" in result.protocol.reinforcement
    assert result.protocol.geometry["h0"] == pytest.approx(
        result.selected_longitudinal.section.effective_depth()
    )


def test_design_rectangular_forwards_load_duration():
    result = design_rectangular_element(mvp_input(load_duration="long"))

    assert result.selected_longitudinal is not None
    assert result.selected_longitudinal.bending.intermediate_values["load_duration"] == "long"


def test_design_rectangular_with_crack_check():
    result = design_rectangular_element(
        mvp_input(check_cracks=True, Mser=30_000_000)
    )

    assert result.status == "pass"
    assert result.crack_formation is not None
    assert result.crack_formation.status == "crack"
    assert result.protocol is not None
    assert "crack_formation" in result.protocol.checks
    assert any("crack width check is required" in warning for warning in result.warnings)
