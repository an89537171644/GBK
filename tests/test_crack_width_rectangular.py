import pytest

from sp63_core.checks import check_normal_crack_width_rectangular
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection


def mvp_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def test_crack_width_not_required_when_no_crack():
    result = check_normal_crack_width_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=10_000_000,
        As=942.48,
        main_bar_diameter=20,
    )

    assert result.status == "not_required"
    assert result.acrc == pytest.approx(0.0)
    assert result.utilization == pytest.approx(0.0)
    assert any("draft crack width check" in warning for warning in result.warnings)
    assert any("not required" in warning for warning in result.warnings)


def test_crack_width_passes_for_moderate_service_moment():
    result = check_normal_crack_width_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=30_000_000,
        As=942.48,
        main_bar_diameter=20,
        acrc_limit=0.3,
    )

    assert result.Mser > result.Mcrc
    assert result.acrc > 0
    assert result.acrc <= result.acrc_limit
    assert result.status == "pass"
    assert result.requires_engineer_review is True


def test_crack_width_fails_for_small_reinforcement_or_high_moment():
    result = check_normal_crack_width_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=80_000_000,
        As=402.12,
        main_bar_diameter=16,
        acrc_limit=0.3,
    )

    assert result.status == "fail"
    assert result.utilization > 1
    assert "crack width exceeds draft limit" in result.warnings


def test_crack_width_uses_Rsser_warning():
    result = check_normal_crack_width_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=90_000_000,
        As=402.12,
        main_bar_diameter=16,
        acrc_limit=0.3,
    )

    assert result.sigma_s > get_rebar("A500").Rsser
    assert "service reinforcement stress exceeds Rsser; engineer review is required" in (
        result.warnings
    )


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("Mser", -1, "Mser must be non-negative"),
        ("As", 0, "As must be positive"),
        ("main_bar_diameter", 0, "main_bar_diameter must be positive"),
        ("acrc_limit", 0, "acrc_limit must be positive"),
    ],
)
def test_crack_width_rejects_invalid_inputs(field, value, match):
    kwargs = {
        "section": mvp_section(),
        "concrete": get_concrete("B25"),
        "rebar": get_rebar("A500"),
        "Mser": 30_000_000,
        "As": 942.48,
        "main_bar_diameter": 20,
        "acrc_limit": 0.3,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=match):
        check_normal_crack_width_rectangular(**kwargs)


@pytest.mark.parametrize(
    ("updates", "match"),
    [
        ({"concrete": get_concrete("B25").model_copy(update={"Rbtser": 0})}, "Rbtser"),
        ({"rebar": get_rebar("A500").model_copy(update={"Es": 0})}, "Es"),
        ({"rebar": get_rebar("A500").model_copy(update={"Rsser": 0})}, "Rsser"),
    ],
)
def test_crack_width_rejects_invalid_material_properties(updates, match):
    kwargs = {
        "section": mvp_section(),
        "concrete": get_concrete("B25"),
        "rebar": get_rebar("A500"),
        "Mser": 30_000_000,
        "As": 942.48,
        "main_bar_diameter": 20,
        "acrc_limit": 0.3,
    }
    kwargs.update(updates)

    with pytest.raises(ValueError, match=match):
        check_normal_crack_width_rectangular(**kwargs)
