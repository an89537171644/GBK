import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_select_longitudinal_rebar_returns_top_five_passing_options():
    options = select_longitudinal_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
    )

    assert len(options) == 5
    assert [option.scheme for option in options] == ["8D12", "6D14", "3D20", "2D25", "5D16"]
    assert [option.As for option in options] == sorted(option.As for option in options)
    assert all(option.bending.status == "pass" for option in options)
    assert all(option.requires_engineer_review is True for option in options)


def test_select_longitudinal_rebar_checks_every_candidate_through_bending():
    options = select_longitudinal_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        bar_counts=(2,),
        diameters=(16, 32),
    )

    assert [option.scheme for option in options] == ["2D32"]
    assert options[0].bending.intermediate_values["As"] == pytest.approx(options[0].As)
    assert options[0].bending.utilization < 1.0


def test_select_longitudinal_rebar_returns_empty_when_no_candidate_passes():
    options = select_longitudinal_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=1_000_000_000,
        bar_counts=(2,),
        diameters=(10,),
    )

    assert options == ()


def test_select_longitudinal_rebar_rejects_invalid_limits():
    with pytest.raises(ValueError, match="max_results must be positive"):
        select_longitudinal_rebar(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            max_results=0,
        )

    with pytest.raises(ValueError, match="bar_count must be positive"):
        select_longitudinal_rebar(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            bar_counts=(0,),
        )
