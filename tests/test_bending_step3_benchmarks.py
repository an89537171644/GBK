import json
from importlib.resources import files
from pathlib import Path

import pytest

from sp63_core.checks import check_bending_rectangular
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.sections import RectangularBendingOrientation, RectangularSection
from sp63_core.validation import run_step3_bending_benchmark_cases

BENCHMARK_PATH = Path("tests/golden_cases/uls_bend_rect_step3_benchmarks.json")


def test_step3_benchmark_suite_is_fail_closed_and_reproducible():
    suite = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    orientation = RectangularBendingOrientation(**suite["orientation"])

    assert suite["decision_status"] == "ASSUMPTION"
    assert suite["completeness_status"] == "incomplete"
    assert suite["evidence_status"] == "needs_engineer_review"
    assert suite["project_use_status"] == "prohibited"
    assert suite["project_use"] is False
    assert suite["requires_engineer_review"] is True
    assert [case["case_id"] for case in suite["cases"]] == [
        "BMR-01",
        "BMR-02",
        "BMR-03",
        "BMR-04",
        "BMR-05",
    ]

    for case in suite["cases"]:
        input_data = case["input"]
        expected = case["expected"]
        section = RectangularSection(
            b=input_data["b"],
            h=input_data["h"],
            cover=input_data["cover"],
            stirrup_diameter=input_data["stirrup_diameter"],
            main_bar_diameter=input_data["main_bar_diameter"],
        )
        As = input_data["bar_count"] * area_by_diameter(
            input_data["main_bar_diameter"]
        )
        As_prime = 0.0
        if input_data["As_prime_bar_count"]:
            As_prime = input_data["As_prime_bar_count"] * area_by_diameter(
                input_data["As_prime_bar_diameter"]
            )
        result = check_bending_rectangular(
            section=section,
            concrete=get_concrete(input_data["concrete_class"]),
            rebar=get_rebar(input_data["rebar_class"]),
            As=As,
            As_prime=As_prime,
            M=input_data["M"],
            orientation=orientation,
            load_duration=input_data["load_duration"],
        )

        assert section.effective_depth() == pytest.approx(expected["h0"])
        _assert_optional_float(result.x, expected["x"])
        _assert_optional_float(result.xi, expected["xi"])
        assert result.xi_R == pytest.approx(expected["xi_R"])
        assert result.intermediate_values["x_limit"] == pytest.approx(
            expected["x_limit"]
        )
        _assert_optional_float(result.Mult, expected["Mult"])
        _assert_optional_float(result.utilization, expected["utilization"])
        assert result.status == expected["status"]
        assert result.capacity_applicable is expected["capacity_applicable"]
        if not result.capacity_applicable:
            assert "Mult" not in result.intermediate_values
            assert "utilization" not in result.intermediate_values
            assert result.intermediate_values["applicability_reason"] == expected[
                "applicability_reason"
            ]
        for key in ("Rb_base", "gamma_b1", "Rb_effective"):
            if key in expected:
                assert result.intermediate_values[key] == pytest.approx(expected[key])


def test_step3_benchmarks_are_part_of_golden_validation():
    results = run_step3_bending_benchmark_cases()

    assert [result.case_id for result in results] == [
        "BMR-01",
        "BMR-02",
        "BMR-03",
        "BMR-04",
        "BMR-05",
    ]
    assert all(result.passed for result in results)
    assert results[3].expected["Mult"] is None
    assert results[4].actual["Mult"] is None
    assert all(
        any("assumption-level" in warning for warning in result.warnings)
        for result in results
    )


def test_packaged_benchmark_fixture_matches_review_fixture():
    packaged = json.loads(
        files("sp63_core.validation")
        .joinpath("data/uls_bend_rect_step3_benchmarks.json")
        .read_text(encoding="utf-8")
    )
    reviewed = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

    assert packaged == reviewed


def _assert_optional_float(actual, expected) -> None:
    if expected is None:
        assert actual is None
    else:
        assert actual == pytest.approx(expected)
