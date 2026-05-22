import pytest

from sp63_core.materials import get_concrete
from sp63_core.rebar import check_transverse_spacing_constructive
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_transverse_spacing_constructive_passes_low_shear_spacing():
    result = check_transverse_spacing_constructive(
        section=mvp_section(),
        Q=80_000,
        concrete=get_concrete("B25"),
        stirrup_diameter=8,
        spacing=300,
    )

    assert result.status == "pass"
    assert result.intermediate_values["transverse_required_by_calculation"] is False
    assert result.intermediate_values["max_spacing"] == pytest.approx(337.5)


def test_transverse_spacing_constructive_fails_when_spacing_too_large_for_required_shear():
    result = check_transverse_spacing_constructive(
        section=mvp_section(),
        Q=160_000,
        concrete=get_concrete("B25"),
        stirrup_diameter=8,
        spacing=300,
    )

    assert result.status == "fail"
    assert result.intermediate_values["transverse_required_by_calculation"] is True
    assert result.intermediate_values["max_spacing"] == pytest.approx(225)
    assert "stirrup spacing exceeds constructive maximum" in result.warnings


def test_transverse_spacing_constructive_rejects_small_diameter():
    result = check_transverse_spacing_constructive(
        section=mvp_section(),
        Q=80_000,
        concrete=get_concrete("B25"),
        stirrup_diameter=4,
        spacing=100,
    )

    assert result.status == "fail"
    assert "stirrup diameter is less than 6 mm for bending elements" in result.warnings
