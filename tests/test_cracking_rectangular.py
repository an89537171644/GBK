import pytest

from sp63_core.checks import check_normal_crack_formation_rectangular
from sp63_core.materials import get_concrete
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_normal_crack_formation_no_crack():
    result = check_normal_crack_formation_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        Mser=10_000_000,
    )

    assert result.intermediate_values["W"] == pytest.approx(12_500_000)
    assert result.Mcrc == pytest.approx(19_375_000)
    assert result.status == "no_crack"
    assert result.utilization < 1
    assert result.requires_engineer_review is True
    assert result.intermediate_values["serviceability_scope"] == "normal_crack_formation_only"
    assert result.intermediate_values["transformed_section_used"] is False
    assert any(
        "draft gross-section crack formation check" in warning
        for warning in result.warnings
    )


def test_normal_crack_formation_crack():
    result = check_normal_crack_formation_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        Mser=30_000_000,
    )

    assert result.status == "crack"
    assert result.utilization > 1
    assert any("crack width check is required" in warning for warning in result.warnings)


def test_normal_crack_formation_rejects_negative_moment():
    with pytest.raises(ValueError):
        check_normal_crack_formation_rectangular(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            Mser=-1,
        )


def test_normal_crack_formation_uses_Rbtser_not_Rbt():
    concrete = get_concrete("B25")
    result = check_normal_crack_formation_rectangular(
        section=mvp_section(),
        concrete=concrete,
        Mser=10_000_000,
    )
    section_modulus = result.intermediate_values["W"]

    assert concrete.Rbt == pytest.approx(1.05)
    assert concrete.Rbtser == pytest.approx(1.55)
    assert result.Mcrc == pytest.approx(concrete.Rbtser * section_modulus)
    assert result.Mcrc != pytest.approx(concrete.Rbt * section_modulus)
