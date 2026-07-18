from sp63_core.validation import (
    GoldenCaseResult,
    run_bending_golden_cases,
    run_crack_formation_golden_cases,
    run_crack_width_golden_cases,
    run_deflection_golden_cases,
    run_design_golden_cases,
    run_shear_golden_cases,
)
from sp63_core.validation.golden import _matches_expected


def test_bending_golden_cases_pass():
    results = run_bending_golden_cases()

    assert results
    assert all(result.passed for result in results)
    assert all(result.status == "pass" for result in results)


def test_shear_golden_case_passes():
    results = run_shear_golden_cases()

    assert results
    assert all(result.passed for result in results)


def test_design_golden_case_passes():
    results = run_design_golden_cases()

    assert results
    assert all(result.passed for result in results)
    assert results[0].expected["strength_status"] == "outside_applicability"
    assert results[0].expected["serviceability_status"] == "not_checked"
    assert results[0].expected["overall_status"] == "outside_applicability"
    assert results[0].actual["strength_status"] == "outside_applicability"
    assert results[0].actual["serviceability_status"] == "not_checked"
    assert results[0].actual["overall_status"] == "outside_applicability"


def test_crack_formation_golden_case_passes():
    results = run_crack_formation_golden_cases()

    assert results
    assert all(result.passed for result in results)


def test_crack_width_golden_case_passes():
    results = run_crack_width_golden_cases()

    assert results
    assert all(result.passed for result in results)


def test_deflection_golden_case_passes():
    results = run_deflection_golden_cases()

    assert results
    assert all(result.passed for result in results)


def test_golden_case_result_contains_expected_and_actual():
    result = run_bending_golden_cases()[0]

    assert isinstance(result, GoldenCaseResult)
    assert result.expected
    assert result.actual
    assert "calculation_status" in result.expected
    assert "calculation_status" in result.actual


def test_golden_comparator_rejects_non_finite_actual_value():
    assert not _matches_expected(
        expected={"value": 1.0},
        actual={"value": float("nan")},
        tolerances={"value": 0.1},
    )
