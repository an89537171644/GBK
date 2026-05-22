import pytest

from sp63_core.materials import get_concrete, get_rebar
from sp63_core.ml import suggest_checked_longitudinal_options
from sp63_core.sections import RectangularSection


def test_suggest_checked_longitudinal_options_returns_only_passed_options():
    suggestion = suggest_checked_longitudinal_options(
        predicted_As=950,
        section=RectangularSection(
            b=300,
            h=500,
            cover=32,
            stirrup_diameter=8,
            main_bar_diameter=20,
        ),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        max_results=5,
    )

    assert suggestion.selected_options
    assert all(option.status == "pass" for option in suggestion.selected_options)
    assert all(option.bending.status == "pass" for option in suggestion.selected_options)
    assert suggestion.unsafe_accept_rate == 0.0
    assert suggestion.requires_deterministic_check is True


def test_suggest_checked_longitudinal_options_sorts_by_predicted_area():
    suggestion = suggest_checked_longitudinal_options(
        predicted_As=950,
        section=RectangularSection(
            b=300,
            h=500,
            cover=32,
            stirrup_diameter=8,
            main_bar_diameter=20,
        ),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=150_000_000,
        max_results=5,
    )

    distances = [abs(option.As - suggestion.predicted_As) for option in suggestion.selected_options]
    assert distances == sorted(distances)


def test_suggest_checked_longitudinal_options_rejects_invalid_limit():
    with pytest.raises(ValueError, match="max_results must be positive"):
        suggest_checked_longitudinal_options(
            predicted_As=950,
            section=RectangularSection(
                b=300,
                h=500,
                cover=32,
                stirrup_diameter=8,
                main_bar_diameter=20,
            ),
            concrete=get_concrete("B25"),
            rebar=get_rebar("A500"),
            M=150_000_000,
            max_results=0,
        )


def test_suggest_checked_longitudinal_options_returns_empty_when_no_candidate_passes():
    suggestion = suggest_checked_longitudinal_options(
        predicted_As=950,
        section=RectangularSection(
            b=300,
            h=500,
            cover=32,
            stirrup_diameter=8,
            main_bar_diameter=20,
        ),
        concrete=get_concrete("B25"),
        rebar=get_rebar("A500"),
        M=10_000_000_000,
        max_results=5,
    )

    assert suggestion.selected_options == ()
    assert suggestion.unsafe_accept_rate == 0.0
    assert suggestion.requires_deterministic_check is True
