import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.rebar import select_longitudinal_rebar
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

ORIENTATION = RectangularBendingOrientation(
    local_axes_id="selection-test-local-axes",
    moment_axis="local_z",
    tension_face="local_y_min",
)


def _select(**kwargs):
    kwargs.setdefault("orientation", ORIENTATION)
    kwargs.setdefault("load_duration", "short")
    return select_longitudinal_rebar(**kwargs)


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_select_longitudinal_rebar_returns_top_five_passing_options():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
    )

    assert len(options) == 5
    assert [option.As for option in options] == sorted(option.As for option in options)
    assert all(option.status == "outside_applicability" for option in options)
    assert all(option.utilization is None for option in options)
    assert all(option.diagnostic_status == "pass" for option in options)
    assert all(option.diagnostic_utilization <= 1.0 for option in options)
    assert all(option.bending.status == "outside_applicability" for option in options)
    assert all(option.bending.Mult is None for option in options)
    assert all(option.bending.utilization is None for option in options)
    assert all(option.bending.capacity_applicable is False for option in options)
    assert all(option.bending.diagnostic_status == "pass" for option in options)
    assert all(option.bending.diagnostic_Mult is not None for option in options)
    assert all(
        option.bending.diagnostic_utilization is not None for option in options
    )
    assert all(
        option.bending.diagnostic_capacity_applicable is True for option in options
    )
    assert all(
        option.bending.capacity_publication_allowed is False for option in options
    )
    assert all(option.constructive.status == "pass" for option in options)
    assert all(
        option.constructive.intermediate_values["reinforcement_ratio_percent"] >= 0.1
        for option in options
    )
    assert all(option.layout.layout_feasible is True for option in options)
    assert all(option.requires_engineer_review is True for option in options)


def test_select_longitudinal_rebar_checks_every_candidate_through_bending():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        bar_counts=(2,),
        diameters=(16, 32),
    )

    assert [option.scheme for option in options] == ["2D32"]
    assert options[0].bending.intermediate_values["As"] == pytest.approx(options[0].As)
    assert options[0].section.main_bar_diameter == 32
    assert options[0].section.effective_depth() == pytest.approx(444)
    assert options[0].utilization is None
    assert options[0].bending.utilization is None
    assert options[0].diagnostic_utilization < 1.0
    assert options[0].bending.diagnostic_utilization is not None
    assert options[0].bending.diagnostic_utilization < 1.0


def test_select_longitudinal_rebar_recalculates_h0_for_each_diameter():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        bar_counts=(3,),
        diameters=(20, 25),
        max_results=2,
    )

    h0_by_diameter = {option.diameter: option.section.effective_depth() for option in options}
    assert h0_by_diameter[20] == pytest.approx(450)
    assert h0_by_diameter[25] == pytest.approx(447.5)


def test_select_longitudinal_rebar_preserves_explicit_orientation():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        bar_counts=(3,),
        diameters=(20,),
        max_results=1,
    )

    assert options[0].bending.intermediate_values["local_axes_id"] == (
        "selection-test-local-axes"
    )
    assert options[0].bending.intermediate_values["tension_face"] == "local_y_min"


def test_select_longitudinal_rebar_filters_infeasible_single_layer_layout():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        bar_counts=(8,),
        diameters=(32,),
    )

    assert options == ()


def test_select_longitudinal_rebar_forwards_load_duration():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        load_duration="long",
    )

    assert options
    assert all(option.bending.intermediate_values["load_duration"] == "long" for option in options)


def test_select_longitudinal_rebar_returns_empty_when_no_candidate_passes():
    options = _select(
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
        _select(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            max_results=0,
        )

    with pytest.raises(ValueError, match="bar_count must be positive"):
        _select(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            bar_counts=(0,),
        )


def test_selector_validates_context_before_empty_enumeration():
    with pytest.raises(TypeError, match="orientation"):
        select_longitudinal_rebar(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            orientation="bad",  # type: ignore[arg-type]
            load_duration="short",
            bar_counts=(),
            diameters=(),
        )

    with pytest.raises(ValueError, match="load_duration"):
        _select(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            load_duration="bogus",
            bar_counts=(),
            diameters=(),
        )


def test_selector_returns_no_options_for_unsupported_longitudinal_material():
    options = _select(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A240"),
        M=150_000_000,
    )

    assert options == ()
