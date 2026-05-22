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


def test_select_transverse_rebar_sorts_by_steel_consumption():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
        max_results=10,
    )

    consumptions = [option.Asw / option.spacing for option in options]
    assert consumptions == sorted(consumptions)


def test_select_transverse_rebar_returns_empty_when_no_candidate_passes():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=2_000_000,
    )

    assert options == ()


def test_select_transverse_rebar_respects_max_results():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
        max_results=3,
    )

    assert len(options) == 3


def test_select_transverse_rebar_rejects_invalid_max_results():
    with pytest.raises(ValueError, match="max_results must be positive"):
        select_transverse_rebar(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            stirrup_rebar=get_rebar("A240"),
            Q=80_000,
            max_results=0,
        )
