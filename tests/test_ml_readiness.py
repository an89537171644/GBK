"""Tests for ML readiness gate."""

from sp63_core.dataset import generate_dataset_cases, generate_diagnostic_dataset_cases
from sp63_core.ml import build_ml_readiness_report


def test_ml_readiness_report_builds_for_generated_dataset():
    cases = generate_dataset_cases(limit=20, load_duration="short")
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.total_rows == 20
    assert report.feature_columns_count > 0
    assert report.target_columns_count > 0
    assert report.requires_engineer_review is True


def test_ml_readiness_report_has_no_missing_required_columns():
    cases = generate_dataset_cases(limit=20, load_duration="short")
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.missing_required_columns == ()


def test_ml_readiness_report_counts_safe_dataset_rows():
    cases = generate_dataset_cases(limit=20, load_duration="short")
    report = build_ml_readiness_report(case.as_row() for case in cases)

    assert report.unsafe_rows_count == 0
    assert report.group_key_present is True
    assert report.unique_group_count > 0
    assert report.group_leakage_count == 0


def test_ml_readiness_warns_for_only_passing_overall_status():
    cases = generate_dataset_cases(limit=20, load_duration="short")
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


def test_ml_readiness_fails_closed_for_legacy_or_missing_v03_provenance():
    case = generate_dataset_cases(limit=1, load_duration="short")[0]

    missing_orientation = case.as_row()
    missing_orientation.pop("local_axes_id")
    missing_report = build_ml_readiness_report((missing_orientation,))

    legacy = case.as_row()
    legacy["dataset_version"] = "0.2"
    legacy_report = build_ml_readiness_report((legacy,))

    assert missing_report.status == "fail"
    assert "local_axes_id" in missing_report.missing_required_columns
    assert legacy_report.status == "fail"
    assert any("provenance is invalid" in warning for warning in legacy_report.warnings)


def test_ml_readiness_warns_for_small_diagnostic_dataset():
    cases = generate_diagnostic_dataset_cases(limit=6)
    report = build_ml_readiness_report(case.as_readiness_row() for case in cases)

    assert report.status == "review_required"
    assert report.missing_required_columns == ()
    assert report.group_key_present is True
    assert report.unique_group_count > 1
    assert "overall_status" not in report.constant_target_columns
    assert any(
        "diagnostic dataset has fewer than 1000 rows" in warning
        for warning in report.warnings
    )


def test_ml_readiness_diagnostic_rows_have_no_provenance_exemption():
    case = generate_diagnostic_dataset_cases(limit=6)[0]

    missing_orientation = case.as_readiness_row()
    missing_orientation.pop("local_axes_id")
    missing_report = build_ml_readiness_report((missing_orientation,))

    invalid_duration = case.as_readiness_row()
    invalid_duration["load_duration"] = "long"
    duration_report = build_ml_readiness_report((invalid_duration,))

    unsafe_project_use = case.as_readiness_row()
    unsafe_project_use["project_use"] = True
    project_use_report = build_ml_readiness_report((unsafe_project_use,))

    assert missing_report.status == "fail"
    assert "local_axes_id" in missing_report.missing_required_columns
    assert duration_report.status == "fail"
    assert any("provenance is invalid" in warning for warning in duration_report.warnings)
    assert project_use_report.status == "fail"
    assert any("provenance is invalid" in warning for warning in project_use_report.warnings)
