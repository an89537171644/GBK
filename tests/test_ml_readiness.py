"""Tests for ML readiness gate."""

from sp63_core.dataset import generate_dataset_cases, generate_diagnostic_dataset_cases
from sp63_core.ml import build_ml_readiness_report


def test_ml_readiness_report_builds_for_generated_dataset():
    cases = generate_dataset_cases(limit=20)
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.total_rows == 20
    assert report.feature_columns_count > 0
    assert report.target_columns_count > 0
    assert report.requires_engineer_review is True


def test_ml_readiness_report_has_no_missing_required_columns():
    cases = generate_dataset_cases(limit=20)
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.missing_required_columns == ()


def test_ml_readiness_report_counts_safe_dataset_rows():
    cases = generate_dataset_cases(limit=20)
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.unsafe_rows_count == 0
    assert report.group_key_present is True
    assert report.unique_group_count > 0
    assert report.group_leakage_count == 0


def test_ml_readiness_warns_for_only_passing_overall_status():
    cases = generate_dataset_cases(limit=20)
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.status == "review_required"
    assert report.status_counts["overall_status"] == {"pass": 20}
    assert "overall_status" in report.constant_target_columns
    assert "overall_status" in report.low_variance_status_columns
    assert any(
        "dataset contains only passing overall_status rows" in warning
        for warning in report.warnings
    )


def test_ml_readiness_fails_when_required_columns_are_missing():
    rows = [
        {
            "section_b_mm": 300.0,
            "overall_status": "pass",
            "unsafe_row": False,
        }
    ]
    report = build_ml_readiness_report(rows)

    assert report.status == "fail"
    assert "section_h_mm" in report.missing_required_columns
    assert any("missing required columns" in warning for warning in report.warnings)


def test_ml_readiness_warns_for_small_diagnostic_dataset():
    cases = generate_diagnostic_dataset_cases(limit=6)
    report = build_ml_readiness_report(case.as_readiness_row() for case in cases)

    assert report.status == "review_required"
    assert report.group_key_present is True
    assert report.unique_group_count > 1
    assert "overall_status" not in report.constant_target_columns
    assert any(
        "diagnostic dataset has fewer than 1000 rows" in warning
        for warning in report.warnings
    )
