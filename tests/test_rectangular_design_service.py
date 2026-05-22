import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection
from sp63_core.services import design_rectangular_element


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_design_rectangular_element_returns_passing_protocol():
    result = design_rectangular_element(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        longitudinal_rebar=get_rebar("A500"),
        transverse_rebar=get_rebar("A240"),
        M=150_000_000,
        Q=80_000,
    )

    assert result.status == "pass"
    assert result.protocol is not None
    assert result.protocol.status == "pass"
    assert result.selected_longitudinal is not None
    assert result.selected_transverse is not None
    assert result.selected_longitudinal.bending.status == "pass"
    assert result.selected_transverse.shear.status == "pass"
    assert result.longitudinal_options
    assert result.transverse_options
    assert result.selected_longitudinal is result.longitudinal_options[0]
    assert result.selected_transverse is result.transverse_options[0]
    assert result.requires_engineer_review is True
    assert result.protocol.requires_engineer_review is True


def test_design_rectangular_element_fails_without_longitudinal_options():
    result = design_rectangular_element(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        longitudinal_rebar=get_rebar("A500"),
        transverse_rebar=get_rebar("A240"),
        M=10_000_000_000,
        Q=80_000,
        longitudinal_max_results=1,
    )

    assert result.status == "fail"
    assert result.protocol is None
    assert result.longitudinal_options == ()
    assert result.transverse_options == ()
    assert result.selected_longitudinal is None
    assert result.selected_transverse is None
    assert result.warnings == ("no passing longitudinal reinforcement options",)


def test_design_rectangular_element_fails_without_transverse_options():
    result = design_rectangular_element(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        longitudinal_rebar=get_rebar("A500"),
        transverse_rebar=get_rebar("A240"),
        M=150_000_000,
        Q=2_000_000,
    )

    assert result.status == "fail"
    assert result.protocol is None
    assert result.longitudinal_options
    assert result.selected_longitudinal is not None
    assert result.transverse_options == ()
    assert result.selected_transverse is None
    assert result.warnings == ("no passing transverse reinforcement options",)


def test_design_rectangular_element_rejects_negative_loads():
    common = {
        "section": mvp_section(),
        "concrete": get_concrete("B25"),
        "longitudinal_rebar": get_rebar("A500"),
        "transverse_rebar": get_rebar("A240"),
    }

    with pytest.raises(ValueError, match="M must be non-negative"):
        design_rectangular_element(**common, M=-1, Q=80_000)

    with pytest.raises(ValueError, match="Q must be non-negative"):
        design_rectangular_element(**common, M=150_000_000, Q=-1)
