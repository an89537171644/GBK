import pytest

from sp63_core.checks import check_shear_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_shear_rectangular_draft_golden_case_pass():
    Asw = 2 * area_by_diameter(8)

    result = check_shear_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Asw=Asw,
        sw=200,
        Q=80_000,
    )

    assert result.qsw == pytest.approx(85.45, rel=1e-3)
    assert result.Q_strip == pytest.approx(587_250, rel=1e-6)
    assert result.intermediate_values["C"] == pytest.approx(900)
    assert result.Qb == pytest.approx(106_310, rel=1e-3)
    assert result.Qsw == pytest.approx(57_680, rel=1e-3)
    assert result.Qult == pytest.approx(163_990, rel=1e-3)
    assert result.status == "pass"
    assert result.warnings == ()
    assert result.requires_engineer_review is True


def test_shear_rectangular_without_stirrups_can_pass_for_low_shear():
    result = check_shear_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Asw=0,
        sw=200,
        Q=70_000,
    )

    assert result.qsw == 0
    assert result.Qult == pytest.approx(106_312.5)
    assert result.status == "pass"


def test_shear_rectangular_fails_when_inclined_section_capacity_is_exceeded():
    result = check_shear_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Asw=2 * area_by_diameter(8),
        sw=200,
        Q=200_000,
    )

    assert result.Q_strip > 200_000
    assert result.Qult < 200_000
    assert result.status == "fail"
    assert "inclined section capacity" in result.warnings[0]


def test_shear_rectangular_fails_when_strip_capacity_is_exceeded():
    result = check_shear_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Asw=2 * area_by_diameter(8),
        sw=200,
        Q=600_000,
    )

    assert result.Q_strip < 600_000
    assert result.status == "fail"
    assert "concrete strip capacity" in result.warnings[0]


def test_shear_rectangular_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="Q must be non-negative"):
        check_shear_rectangular(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            stirrup_rebar=get_rebar("A240"),
            Asw=2 * area_by_diameter(8),
            sw=200,
            Q=-1,
        )

    with pytest.raises(ValueError, match="Asw must be non-negative"):
        check_shear_rectangular(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            stirrup_rebar=get_rebar("A240"),
            Asw=-1,
            sw=200,
            Q=80_000,
        )

    with pytest.raises(ValueError, match="sw must be positive"):
        check_shear_rectangular(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            stirrup_rebar=get_rebar("A240"),
            Asw=2 * area_by_diameter(8),
            sw=0,
            Q=80_000,
        )
