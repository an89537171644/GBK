"""Tests for the K23 diagnostic dataset."""

import csv
import json
from dataclasses import replace

import pytest

from sp63_core.cli import main
from sp63_core.dataset import (
    DATASET_VERSION,
    DIAGNOSTIC_DATASET_SOURCE,
    diagnostic_status_counts,
    diagnostic_unique_group_count,
    generate_diagnostic_dataset_cases,
    split_diagnostic_dataset_by_group,
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
    cases_1000 = generate_diagnostic_dataset_cases(limit=1000)

    assert len(cases_50) == 50
    assert len(cases_100) == 100
    assert len(cases_1000) == 1000
    assert cases_50[:6] == cases_100[:6]
    assert cases_100[:6] == cases_1000[:6]
    assert diagnostic_unique_group_count(cases_1000) >= 50


def test_generate_diagnostic_dataset_cases_supports_5000_row_smoke():
    cases = generate_diagnostic_dataset_cases(limit=5000)

    assert len(cases) == 5000
    assert diagnostic_unique_group_count(cases) >= 50


def test_generate_diagnostic_dataset_cases_contains_pass_fail_review_statuses():
    cases = generate_diagnostic_dataset_cases(limit=100)
    overall_statuses = {case.overall_status for case in cases}

    assert {"pass", "fail", "review_or_fail"} <= overall_statuses


def test_generate_diagnostic_dataset_cases_marks_review_and_source():
    cases = generate_diagnostic_dataset_cases(limit=50)

    assert all(case.requires_engineer_review is True for case in cases)
    assert all(case.dataset_source == DIAGNOSTIC_DATASET_SOURCE for case in cases)
    assert all(case.dataset_version == DATASET_VERSION for case in cases)
    assert all(case.local_axes_id for case in cases)
    assert all(case.moment_axis == "local_z" for case in cases)
    assert all(case.tension_face == "local_y_min" for case in cases)
    assert all(case.load_duration == "short" for case in cases)
    assert all(case.completeness_status == "incomplete" for case in cases)
    assert all(case.evidence_status == "needs_engineer_review" for case in cases)
    assert all(case.project_use_status == "prohibited" for case in cases)
    assert all(case.project_use is False for case in cases)
    assert all(case.group_key for case in cases)
    assert diagnostic_unique_group_count(cases) > 1
    assert all(
        case.failure_reason
        for case in cases
        if case.overall_status in ("fail", "review_or_fail")
    )


def test_diagnostic_row_and_csv_preserve_versioned_safety_provenance(tmp_path):
    case = generate_diagnostic_dataset_cases(limit=6)[0]
    row = case.as_readiness_row()
    output_path = tmp_path / "diagnostic.csv"

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=tuple(row))
        writer.writeheader()
        writer.writerow(row)
    with output_path.open(newline="", encoding="utf-8") as file:
        csv_row = next(csv.DictReader(file))

    assert row["dataset_version"] == DATASET_VERSION
    assert row["local_axes_id"] == case.local_axes_id
    assert row["moment_axis"] == "local_z"
    assert row["tension_face"] == "local_y_min"
    assert row["load_duration"] == "short"
    assert row["completeness_status"] == "incomplete"
    assert row["evidence_status"] == "needs_engineer_review"
    assert row["project_use_status"] == "prohibited"
    assert row["project_use"] is False
    assert row["requires_engineer_review"] is True
    assert csv_row["dataset_version"] == DATASET_VERSION
    assert csv_row["local_axes_id"] == case.local_axes_id
    assert csv_row["load_duration"] == "short"
    assert csv_row["project_use"] == "False"


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("dataset_version", "0.2"),
        ("local_axes_id", ""),
        ("moment_axis", "local_y"),
        ("tension_face", "unknown"),
        ("load_duration", "long"),
        ("completeness_status", "complete"),
        ("evidence_status", "confirmed"),
        ("project_use_status", "allowed"),
        ("project_use", True),
        ("requires_engineer_review", False),
    ),
)
def test_diagnostic_case_rejects_incomplete_or_unsafe_provenance(
    field_name,
    invalid_value,
):
    case = generate_diagnostic_dataset_cases(limit=6)[0]

    with pytest.raises(ValueError):
        replace(case, **{field_name: invalid_value})


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


def test_split_diagnostic_dataset_by_group_has_no_group_leakage():
    cases = generate_diagnostic_dataset_cases(limit=1000)
    split = split_diagnostic_dataset_by_group(cases)
    train_groups = {case.group_key for case in split.train}
    test_groups = {case.group_key for case in split.test}

    assert split.group_leakage_count == 0
    assert train_groups.isdisjoint(test_groups)
    assert len(train_groups) > 1
    assert len(test_groups) > 1
    assert {case.overall_status for case in cases} >= {"pass", "fail", "review_or_fail"}


def test_cli_diagnostic_dataset_json_output(capsys):
    exit_code = main(["diagnostic-dataset", "--limit", "1000", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "diagnostic-dataset"
    assert data["status"] == "pass"
    assert data["case_count"] == 1000
    assert data["unique_group_count"] >= 50
    assert data["group_key_present"] is True
    assert data["group_leakage_count"] == 0
    assert data["status_counts"]["overall_status"]["pass"] >= 1
    assert data["status_counts"]["overall_status"]["fail"] >= 1
    assert data["status_counts"]["overall_status"]["review_or_fail"] >= 1
    assert data["status_counts"]["failure_reason"]["bending capacity fails"] >= 1
    assert all(row["requires_engineer_review"] for row in data["rows"])
    assert all(row["dataset_version"] == DATASET_VERSION for row in data["rows"])
    assert all(row["local_axes_id"] for row in data["rows"])
    assert all(row["moment_axis"] == "local_z" for row in data["rows"])
    assert all(row["tension_face"] == "local_y_min" for row in data["rows"])
    assert all(row["load_duration"] == "short" for row in data["rows"])
    assert all(row["project_use"] is False for row in data["rows"])


def test_cli_ml_readiness_diagnostic_json_output(capsys):
    exit_code = main(["ml-readiness", "--diagnostic", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "ml-readiness"
    assert data["dataset_mode"] == "diagnostic"
    assert data["missing_required_columns"] == []
    assert data["group_key_present"] is True
    assert data["unique_group_count"] >= 50
    assert data["group_leakage_count"] == 0
    assert "overall_status" not in data["constant_target_columns"]
    assert data["status_counts"]["overall_status"]["pass"] >= 1
    assert data["status_counts"]["overall_status"]["fail"] >= 1
    assert data["status_counts"]["overall_status"]["review_or_fail"] >= 1
    assert any("fewer than 1000 rows" in warning for warning in data["warnings"])
