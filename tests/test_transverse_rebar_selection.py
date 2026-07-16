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
    assert all(option.constructive.status in ("pass", "warning") for option in options)
    assert all(
        "stirrup spacing exceeds shear rule maximum for counting transverse reinforcement"
        not in option.shear.warnings
        for option in options
    )
    assert all(
        "qsw is below draft minimum rule for counting transverse reinforcement"
        not in option.shear.warnings
        for option in options
    )
    assert all(
        option.shear.intermediate_values["transverse_reinforcement_countable"] is True
        for option in options
    )
    assert all(option.utilization <= 1.0 for option in options)
    assert all(option.requires_engineer_review is True for option in options)
    assert all(option.section.stirrup_diameter == option.diameter for option in options)
    assert all(
        option.shear.intermediate_values["h0"]
        == pytest.approx(option.section.effective_depth())
        for option in options
    )


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


def test_select_transverse_rebar_includes_constructive_values():
    options = select_transverse_rebar(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
    )

    assert all(
        option.spacing <= option.constructive.intermediate_values["max_spacing"]
        for option in options
    )
    assert all(
        option.steel_consumption == pytest.approx(option.Asw / option.spacing)
        for option in options
    )


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


def test_transverse_candidates_rebuild_geometry_for_each_diameter():
    section = RectangularSection(
        b=150,
        h=300,
        cover=25,
        stirrup_diameter=6,
        main_bar_diameter=18,
    )
    options = select_transverse_rebar(
        section=section,
        concrete=get_concrete("B40"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
        diameters=(8,),
    )

    assert options
    assert all(option.section.stirrup_diameter == 8 for option in options)
    assert all(option.section.effective_depth() == pytest.approx(258) for option in options)
    assert all(option.shear.intermediate_values["h0"] == pytest.approx(258) for option in options)
