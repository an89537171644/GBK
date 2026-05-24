from sp63_core.validation import (
    ManualVerificationCase,
    ManualVerificationResult,
    run_manual_verification_cases,
)


def test_manual_verification_cases_all_pass():
    results = run_manual_verification_cases()

    assert len(results) == 6
    assert all(isinstance(result, ManualVerificationResult) for result in results)
    assert all(result.passed for result in results)
    assert all(result.status == "pass" for result in results)
    assert all(result.requires_engineer_review is True for result in results)


def test_manual_verification_case_shapes_include_required_fields():
    # The public case dataclass is part of the K20 validation contract.
    case = ManualVerificationCase(
        case_id="shape",
        title="shape",
        description="shape",
        inputs={},
        expected_values={},
        tolerances={},
        expected_statuses={},
        source_note="manual",
    )

    assert case.requires_engineer_review is True
    assert case.case_id == "shape"


def test_manual_verification_cases_check_group_statuses():
    results = {result.case_id: result for result in run_manual_verification_cases()}

    assert results["manual_case_01"].actual_statuses["strength_status"] == "pass"
    assert results["manual_case_01"].actual_statuses["serviceability_status"] == "pass"
    assert results["manual_case_01"].actual_statuses["overall_status"] == "pass"

    assert results["manual_case_02"].actual_statuses["strength_status"] == "fail"
    assert results["manual_case_02"].actual_statuses["overall_status"] == "fail"

    assert results["manual_case_03"].actual_statuses["serviceability_status"] == (
        "review_or_fail"
    )
    assert results["manual_case_03"].actual_statuses["overall_status"] == "review_or_fail"

    assert results["manual_case_04"].actual_statuses["serviceability_status"] == "fail"
    assert results["manual_case_05"].actual_statuses["serviceability_status"] == "fail"
    assert results["manual_case_06"].actual_statuses["strength_status"] == "fail"


def test_manual_verification_cases_include_expected_warnings():
    results = {result.case_id: result for result in run_manual_verification_cases()}

    assert results["manual_case_03"].actual_values["crack_warning_present"] is True
    assert results["manual_case_04"].actual_values["Rsser_warning_present"] is True
    assert results["manual_case_04"].actual_values["crack_width_warning_present"] is True
    assert results["manual_case_05"].actual_values["deflection_warning_present"] is True
    assert results["manual_case_06"].actual_values["qsw_warning_present"] is True


def test_manual_verification_case_values_are_within_tolerances():
    for result in run_manual_verification_cases():
        for name, expected in result.expected_values.items():
            actual = result.actual_values[name]
            if isinstance(expected, float):
                assert abs(float(actual) - expected) <= result.tolerances.get(name, 0.0)
            else:
                assert actual == expected
