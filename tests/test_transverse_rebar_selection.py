import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.rebar import select_transverse_rebar
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_select_transverse_rebar_returns_passing_options():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
    )

    assert options
    assert all(option.status == "pass" for option in options)
    assert all(option.shear.status == "pass" for option in options)
    assert all(option.utilization <= 1.0 for option in options)
    assert all(option.requires_engineer_review is True for option in options)


def test_select_transverse_rebar_sorted_by_steel_per_meter():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
    )

    sort_keys = [
        (option.steel_per_meter, -option.spacing, option.diameter, option.legs)
        for option in options
    ]
    assert sort_keys == sorted(sort_keys)


def test_select_transverse_rebar_returns_empty_when_no_candidate_passes():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=2_000_000,
    )

    assert options == ()


def test_select_transverse_rebar_rejects_invalid_options():
    common = {
        "section": mvp_section(),
        "concrete": get_concrete("B25"),
        "stirrup_rebar": get_rebar("A240"),
        "Q": 80_000,
    }

    with pytest.raises(ValueError, match="max_results must be positive"):
        select_transverse_rebar(**common, max_results=0)

    with pytest.raises(ValueError, match="legs must be positive"):
        select_transverse_rebar(**common, legs_options=(0,))

    with pytest.raises(ValueError, match="diameter must be positive"):
        select_transverse_rebar(**common, diameters=(0,))

    with pytest.raises(ValueError, match="spacing must be positive"):
        select_transverse_rebar(**common, spacing_options=(0,))
