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


def test_rejected_geometry_overrides_are_not_section_fields():
    fields = RectangularSection.__dataclass_fields__

    assert "h0_override" not in fields
    assert "compression_bar_diameter" not in fields


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


def test_rejected_h0_override_is_not_accepted_by_constructor():
    with pytest.raises(TypeError, match="h0_override"):
        RectangularSection(
            b=300,
            h=500,
            cover=30,
            stirrup_diameter=8,
            main_bar_diameter=20,
            h0_override=455,
        )
