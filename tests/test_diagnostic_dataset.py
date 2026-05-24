"""Tests for the K23 diagnostic dataset."""

import json

from sp63_core.cli import main
from sp63_core.dataset import (
    DIAGNOSTIC_DATASET_SOURCE,
    diagnostic_status_counts,
    generate_diagnostic_dataset_cases,
)


def test_generate_diagnostic_dataset_cases_contains_required_cases():
    cases = generate_diagnostic_dataset_cases()

    assert len(cases) >= 6
    assert {case.case_type for case in cases} >= {
        "pass_base_beam",
        "bending_fail_low_as",
        "crack_review_without_width",
        "crack_width_fail",
        "deflection_fail",
        "shear_fail",
        "pass_base",
        "bending_fail",
        "multiple_fail",
    }


def test_generate_diagnostic_dataset_cases_honors_expanded_limits():
    cases_50 = generate_diagnostic_dataset_cases(limit=50)
    cases_100 = generate_diagnostic_dataset_cases(limit=100)

    assert len(cases_50) == 50
    assert len(cases_100) == 100
    assert cases_50[:6] == cases_100[:6]


def test_generate_diagnostic_dataset_cases_contains_pass_fail_review_statuses():
    cases = generate_diagnostic_dataset_cases(limit=100)
    overall_statuses = {case.overall_status for case in cases}

    assert {"pass", "fail", "review_or_fail"} <= overall_statuses


def test_generate_diagnostic_dataset_cases_marks_review_and_source():
    cases = generate_diagnostic_dataset_cases(limit=50)

    assert all(case.requires_engineer_review is True for case in cases)
    assert all(case.dataset_source == DIAGNOSTIC_DATASET_SOURCE for case in cases)
    assert all(
        case.failure_reason
        for case in cases
        if case.overall_status in ("fail", "review_or_fail")
    )


def test_diagnostic_status_counts_include_overall_distribution():
    cases = generate_diagnostic_dataset_cases(limit=100)
    counts = diagnostic_status_counts(cases)

    assert counts["overall_status"]["pass"] >= 1
    assert counts["overall_status"]["fail"] >= 1
    assert counts["overall_status"]["review_or_fail"] >= 1
    assert counts["failure_reason"]["bending capacity fails"] >= 1
    assert counts["failure_reason"]["shear capacity fails"] >= 1
    assert counts["failure_reason"]["crack width exceeds draft limit"] >= 1
    assert counts["failure_reason"]["deflection exceeds draft limit"] >= 1


def test_cli_diagnostic_dataset_json_output(capsys):
    exit_code = main(["diagnostic-dataset", "--limit", "100", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "diagnostic-dataset"
    assert data["status"] == "pass"
    assert data["case_count"] == 100
    assert data["status_counts"]["overall_status"]["pass"] >= 1
    assert data["status_counts"]["overall_status"]["fail"] >= 1
    assert data["status_counts"]["overall_status"]["review_or_fail"] >= 1
    assert data["status_counts"]["failure_reason"]["bending capacity fails"] >= 1
    assert all(row["requires_engineer_review"] for row in data["rows"])


def test_cli_ml_readiness_diagnostic_json_output(capsys):
    exit_code = main(["ml-readiness", "--diagnostic", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-readiness"
    assert data["dataset_mode"] == "diagnostic"
    assert data["missing_required_columns"] == []
    assert "overall_status" not in data["constant_target_columns"]
    assert data["status_counts"]["overall_status"]["pass"] >= 1
    assert data["status_counts"]["overall_status"]["fail"] >= 1
    assert data["status_counts"]["overall_status"]["review_or_fail"] >= 1
    assert not any("diagnostic dataset is small" in warning for warning in data["warnings"])
