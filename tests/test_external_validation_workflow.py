import csv
import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.validation import (
    EXTERNAL_VALIDATION_COLUMNS,
    EXTERNAL_VALUES_REQUIRED_WARNING,
    build_external_validation_summary,
)

TEMPLATE_PATH = Path("docs/validation/templates/external_validation_cases_template.csv")
SAMPLE_PATH = Path("tests/fixtures/external_validation_sample.csv")


def test_external_validation_template_exists_with_required_columns():
    assert TEMPLATE_PATH.exists()
    with TEMPLATE_PATH.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)

    assert header == list(EXTERNAL_VALIDATION_COLUMNS)


def test_external_validation_summary_review_required_for_missing_values():
    summary = build_external_validation_summary((_row_with_missing_external_values(),))

    assert summary.status == "review_required"
    assert summary.missing_external_values_count == 1
    assert EXTERNAL_VALUES_REQUIRED_WARNING in summary.warnings


def test_external_validation_summary_passes_for_accepted_rows():
    summary = build_external_validation_summary((_accepted_row(),))

    assert summary.status == "pass"
    assert summary.total_cases == 1
    assert summary.accepted_cases == 1
    assert summary.failed_cases == 0
    assert summary.max_bending_delta_percent == 0.5
    assert summary.max_shear_delta_percent == 0.75
    assert summary.max_crack_width_delta_mm == 0.001
    assert summary.max_deflection_delta_mm == 0.1
    assert summary.requires_engineer_review is True


def test_external_validation_summary_fails_for_failed_rows():
    row = {**_accepted_row(), "acceptance_status": "failed"}
    summary = build_external_validation_summary((row,))

    assert summary.status == "fail"
    assert summary.failed_cases == 1
    assert "external validation contains failed comparison rows" in summary.warnings


def test_cli_external_validation_template_output(capsys):
    exit_code = main(["external-validation", "--template"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "External validation template" in captured.out
    assert "external_validation_cases_template.csv" in captured.out


def test_cli_external_validation_json_output(capsys):
    exit_code = main(["external-validation", "--csv", str(SAMPLE_PATH), "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "external-validation"
    assert data["status"] == "pass"
    assert data["summary"]["total_cases"] == 1
    assert data["summary"]["accepted_cases"] == 1


def _row_with_missing_external_values() -> dict[str, str]:
    row = _accepted_row()
    row["external_bending_mult_nmm"] = ""
    row["acceptance_status"] = "review_required"
    return row


def _accepted_row() -> dict[str, str]:
    return {
        "case_id": "external_case_01",
        "source_type": "manual",
        "element_type": "rectangular_beam",
        "b_mm": "300",
        "h_mm": "500",
        "cover_mm": "32",
        "concrete_class": "B25",
        "main_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "moment_nmm": "150000000",
        "shear_n": "80000",
        "moment_service_nmm": "30000000",
        "span_mm": "6000",
        "program_bending_mult_nmm": "200000000",
        "external_bending_mult_nmm": "201000000",
        "program_shear_qult_n": "120000",
        "external_shear_qult_n": "120900",
        "program_mcrc_nmm": "19375000",
        "external_mcrc_nmm": "19400000",
        "program_crack_width_mm": "0.120",
        "external_crack_width_mm": "0.121",
        "program_deflection_mm": "18.5",
        "external_deflection_mm": "18.6",
        "program_strength_status": "pass",
        "external_strength_status": "pass",
        "program_serviceability_status": "pass",
        "external_serviceability_status": "pass",
        "program_overall_status": "pass",
        "external_overall_status": "pass",
        "delta_bending_percent": "0.5",
        "delta_shear_percent": "0.75",
        "delta_mcrc_percent": "0.13",
        "delta_crack_width_mm": "0.001",
        "delta_deflection_mm": "0.1",
        "acceptance_status": "accepted",
        "engineer_comment": "synthetic public fixture",
        "requires_engineer_review": "true",
    }
