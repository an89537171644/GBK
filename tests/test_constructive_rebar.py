import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.rebar import (
    check_longitudinal_constructive,
    check_transverse_constructive,
)
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_longitudinal_constructive_passes_minimum_ratio():
    result = check_longitudinal_constructive(
        section=mvp_section(),
        bar_count=3,
        As=942.48,
    )

    assert result.status == "pass"
    assert result.intermediate_values["reinforcement_ratio_percent"] >= 0.1


def test_longitudinal_constructive_fails_below_minimum_ratio():
    result = check_longitudinal_constructive(
        section=mvp_section(),
        bar_count=2,
        As=50,
    )

    assert result.status == "fail"
    assert "longitudinal reinforcement ratio is below minimum constructive value" in (
        result.warnings
    )


def test_longitudinal_constructive_requires_two_bars_for_wide_beam():
    result = check_longitudinal_constructive(
        section=mvp_section(),
        bar_count=1,
        As=500,
    )

    assert result.status == "fail"
    assert "beam width greater than 150 mm requires at least two tensile bars" in result.warnings


def test_transverse_constructive_passes_spacing_when_shear_requires_stirrups():
    result = check_transverse_constructive(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=160_000,
        stirrup_diameter=8,
        Asw=100.53,
        spacing=200,
    )

    assert result.status == "pass"
    assert result.intermediate_values["transverse_required_by_calculation"] is True
    assert result.intermediate_values["max_spacing"] == pytest.approx(225)


def test_transverse_constructive_fails_large_spacing_when_shear_requires_stirrups():
    result = check_transverse_constructive(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=160_000,
        stirrup_diameter=8,
        Asw=100.53,
        spacing=300,
    )

    assert result.status == "fail"
    assert result.intermediate_values["max_spacing"] == pytest.approx(225)
    assert "stirrup spacing exceeds constructive maximum" in result.warnings


def test_transverse_constructive_rejects_small_stirrup_diameter():
    result = check_transverse_constructive(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        stirrup_rebar=get_rebar("A240"),
        Q=80_000,
        stirrup_diameter=4,
        Asw=100.53,
        spacing=100,
    )

    assert result.status == "fail"
    assert "stirrup diameter is less than 6 mm for bending elements" in result.warnings
