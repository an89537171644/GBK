from math import inf

import pytest

from sp63_core.checks import check_bending_rectangular
from sp63_core.materials import get_concrete, get_rebar
from sp63_core.sections import RectangularSection


def golden_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=20,
    )


def overreinforced_section() -> RectangularSection:
    return RectangularSection(
        b=300,
        h=500,
        cover=32,
        stirrup_diameter=8,
        main_bar_diameter=25,
    )


def test_bending_rectangular_draft_golden_case_pass():
    result = check_bending_rectangular(
        section=golden_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        As=942.48,
        As_prime=0,
        M=150_000_000,
    )

    assert result.x == pytest.approx(94.25, rel=1e-4)
    assert result.xi == pytest.approx(0.209, rel=3e-3)
    assert result.xi_R == pytest.approx(0.493, rel=2e-3)
    assert result.Mult == pytest.approx(165_170_000, rel=1e-3)
    assert result.utilization == pytest.approx(0.908, rel=2e-3)
    assert result.status == "pass"
    assert result.warnings == ()
    assert result.intermediate_values["h0"] == pytest.approx(450)
    assert result.intermediate_values["source_clause"] == "SP 63.13330.2018 8.1.8-8.1.9"
    assert result.requires_engineer_review is True
    assert result.intermediate_values["requires_engineer_review"] is True


def test_bending_rectangular_draft_golden_case_fail_by_moment():
    result = check_bending_rectangular(
        section=golden_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        As=402.12,
        As_prime=0,
        M=150_000_000,
    )

    assert result.x == pytest.approx(40.21, rel=1e-4)
    assert result.Mult == pytest.approx(75_200_000, rel=1e-3)
    assert result.utilization == pytest.approx(1.995, rel=2e-3)
    assert result.status == "fail"


def test_bending_rectangular_overreinforced_requires_review():
    result = check_bending_rectangular(
        section=overreinforced_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        As=3_926.99,
        As_prime=0,
        M=100_000_000,
    )

    assert result.x > result.xi_R * result.intermediate_values["h0"]
    assert result.status == "review_or_fail"
    assert result.warnings
    assert (
        result.warnings[0]
        == "compression zone height exceeds xi_R * h0; engineering review required"
    )


def test_bending_rectangular_rejects_negative_As():
    with pytest.raises(ValueError, match="As must be non-negative"):
        check_bending_rectangular(
            section=golden_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            As=-1,
            M=150_000_000,
        )


def test_bending_rectangular_rejects_negative_M():
    with pytest.raises(ValueError, match="M must be non-negative"):
        check_bending_rectangular(
            section=golden_section(),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            As=942.48,
            M=-1,
        )


def test_bending_rectangular_zero_reinforcement_fails_with_warning():
    result = check_bending_rectangular(
        section=golden_section(),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        As=0,
        As_prime=0,
        M=100_000_000,
    )

    assert result.x == 0
    assert result.status == "fail"
    assert result.Mult == 0.0
    assert result.utilization == inf
    assert result.warnings == ("non-positive compression zone height",)
