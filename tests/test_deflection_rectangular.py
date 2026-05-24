import pytest

from sp63_core.checks import check_curvature_deflection_rectangular
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


def test_deflection_no_crack_uses_gross_stiffness_and_passes():
    result = check_curvature_deflection_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=10_000_000,
        As=942.48,
        span=6000,
    )

    assert result.status == "pass"
    assert result.stiffness_status == "gross_uncracked"
    assert result.I_eff == pytest.approx(result.I_gross)
    assert result.deflection <= result.deflection_limit
    assert result.requires_engineer_review is True


def test_deflection_cracked_uses_transformed_stiffness():
    result = check_curvature_deflection_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=30_000_000,
        As=942.48,
        span=6000,
    )

    assert result.stiffness_status == "draft_cracked_transformed"
    assert result.I_eff == pytest.approx(result.I_cracked)
    assert result.I_cracked < result.I_gross
    assert result.curvature > 0
    assert result.deflection > 0
    assert result.requires_engineer_review is True
    assert any("cracked transformed stiffness" in warning for warning in result.warnings)


def test_deflection_fails_for_large_span():
    result = check_curvature_deflection_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=80_000_000,
        As=402.12,
        span=12_000,
    )

    assert result.status == "fail"
    assert result.utilization > 1
    assert "deflection exceeds draft limit" in result.warnings


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("Mser", -1, "Mser must be non-negative"),
        ("As", 0, "As must be positive"),
        ("span", 0, "span must be positive"),
        ("deflection_limit_ratio", 0, "deflection_limit_ratio must be positive"),
        ("deflection_limit", 0, "deflection_limit must be positive"),
    ],
)
def test_deflection_rejects_invalid_inputs(field, value, match):
    kwargs = {
        "section": mvp_section(),
        "concrete": get_concrete("B25"),
        "rebar": get_rebar("A500"),
        "Mser": 30_000_000,
        "As": 942.48,
        "span": 6000,
        "deflection_limit": None,
        "deflection_limit_ratio": 250.0,
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=match):
        check_curvature_deflection_rectangular(**kwargs)


def test_deflection_rejects_unsupported_loading_scheme():
    with pytest.raises(ValueError, match="loading_scheme"):
        check_curvature_deflection_rectangular(
            section=mvp_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            Mser=30_000_000,
            As=942.48,
            span=6000,
            loading_scheme="cantilever",
        )


def test_deflection_zero_moment_has_zero_curvature_and_deflection():
    result = check_curvature_deflection_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=0,
        As=942.48,
        span=6000,
    )

    assert result.curvature == pytest.approx(0.0)
    assert result.deflection == pytest.approx(0.0)
    assert result.status == "pass"
    assert any("draft deflection check" in warning for warning in result.warnings)


def test_deflection_intermediate_values_include_key_terms():
    result = check_curvature_deflection_rectangular(
        section=mvp_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        Mser=30_000_000,
        As=942.48,
        span=6000,
    )

    for key in ("I_gross", "I_cracked", "I_eff", "curvature", "deflection"):
        assert key in result.intermediate_values
