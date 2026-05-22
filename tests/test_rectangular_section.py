import pytest

from sp63_core.sections import RectangularSection


def test_effective_depth():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    assert section.effective_depth() == 452


def test_gross_area():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    assert section.gross_area() == 150_000


def test_compression_rebar_depth_with_dedicated_bar():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
        compression_bar_diameter=16,
    )

    assert section.compression_rebar_depth() == 46


def test_compression_rebar_depth_uses_main_bar_as_mvp_simplification():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    assert section.compression_rebar_depth() == 48


def test_invalid_b_raises():
    section = RectangularSection(
        b=0,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    with pytest.raises(ValueError, match="b must be positive"):
        section.validate_geometry()


def test_invalid_h_raises():
    section = RectangularSection(
        b=300,
        h=-1,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    with pytest.raises(ValueError, match="h must be positive"):
        section.validate_geometry()


def test_non_positive_effective_depth_raises():
    section = RectangularSection(
        b=300,
        h=40,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )

    with pytest.raises(ValueError, match="effective depth h0 must be positive"):
        section.validate_geometry()


def test_h0_override_is_used_in_effective_depth():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
        h0_override=455,
    )

    assert section.effective_depth() == 455


def test_non_positive_h0_override_raises():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
        h0_override=0,
    )

    with pytest.raises(ValueError, match="h0_override must be positive"):
        section.validate_geometry()


def test_h0_override_must_be_less_than_section_height():
    section = RectangularSection(
        b=300,
        h=500,
        cover=30,
        stirrup_diameter=8,
        main_bar_diameter=20,
        h0_override=500,
    )

    with pytest.raises(ValueError, match="h0_override must be less than section height"):
        section.validate_geometry()
