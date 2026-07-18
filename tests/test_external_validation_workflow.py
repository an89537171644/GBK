import csv
import json
from pathlib import Path

import pytest

from sp63_core.cli import main
from sp63_core.validation import (
    EXTERNAL_VALIDATION_COLUMNS,
    EXTERNAL_VALUES_REQUIRED_WARNING,
    ExternalValidationTolerance,
    build_external_validation_summary,
    load_external_validation_csv,
)

TEMPLATE_PATH = Path("docs/validation/templates/external_validation_cases_template.csv")
ENGINEER_TEMPLATE_PATH = Path(
    "docs/validation/templates/external_validation_engineer_input_template.csv"
)
CHECKLIST_PATH = Path("docs/validation/external_validation_engineer_checklist.md")
SAMPLE_PATH = Path("tests/fixtures/external_validation_sample.csv")
FILLED_SAMPLE_PATH = Path("docs/validation/samples/external_validation_filled_sample.csv")


def test_external_validation_template_exists_with_required_columns():
    assert TEMPLATE_PATH.exists()
    with TEMPLATE_PATH.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)

    assert header == list(EXTERNAL_VALIDATION_COLUMNS)


def test_external_validation_engineer_template_and_checklist_exist():
    assert ENGINEER_TEMPLATE_PATH.exists()
    with ENGINEER_TEMPLATE_PATH.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader)

    assert header == list(EXTERNAL_VALIDATION_COLUMNS)
    assert CHECKLIST_PATH.exists()
    checklist = CHECKLIST_PATH.read_text(encoding="utf-8")
    assert "external-validation --csv" in checklist
    assert "closed model files" in checklist.lower()


def test_external_validation_summary_review_required_for_missing_values():
    summary = build_external_validation_summary((_row_with_missing_external_values(),))

    assert summary.status == "review_required"
    assert summary.missing_external_values_count == 1
    assert EXTERNAL_VALUES_REQUIRED_WARNING in summary.warnings


def test_external_validation_strict_review_required_for_missing_values():
    summary = build_external_validation_summary(
        (_row_with_missing_external_values(),),
        strict_mode=True,
    )

    assert summary.status == "review_required"
    assert summary.strict_mode is True
    assert summary.missing_required_external_values_count == 1
    assert summary.inconsistent_acceptance_status_count == 0


def test_external_validation_summary_requires_review_for_unapproved_policy():
    summary = build_external_validation_summary((_accepted_row(),))

    assert summary.status == "review_required"
    assert summary.total_cases == 1
    assert summary.accepted_cases == 1
    assert summary.failed_cases == 0
    assert summary.max_bending_delta_percent == 0.5
    assert summary.max_shear_delta_percent == 0.75
    assert summary.max_mcrc_delta_percent == pytest.approx(0.12903225806451613)
    assert summary.max_crack_width_delta_mm == pytest.approx(0.001)
    assert summary.max_deflection_delta_mm == pytest.approx(0.01)
    assert summary.requires_engineer_review is True
    assert summary.completeness_status == "incomplete"
    assert summary.evidence_status == "needs_engineer_review"
    assert summary.project_use_status == "prohibited"
    assert summary.project_use is False
    assert summary.tolerance_policy_status == "ASSUMPTION"
    assert summary.source_adapter_status == "OPEN_QUESTION"
    assert summary.external_validation_status == "NOT_STARTED"
    assert "unapproved diagnostic policy" in " ".join(summary.warnings)


def test_external_validation_summary_fails_closed_for_missing_provenance():
    row = _accepted_row()
    row.pop("local_axes_id")

    summary = build_external_validation_summary((row,))

    assert summary.status == "fail"
    assert summary.invalid_provenance_count == 1
    assert "calculation provenance" in " ".join(summary.warnings)


def test_external_validation_summary_fails_closed_for_long_duration():
    row = {**_accepted_row(), "load_duration": "long"}

    summary = build_external_validation_summary((row,))

    assert summary.status == "fail"
    assert summary.invalid_provenance_count == 1


@pytest.mark.parametrize("invalid_value", ("nan", "inf", "-inf", "-1"))
def test_external_validation_summary_rejects_invalid_numeric_input(invalid_value):
    row = {**_accepted_row(), "external_bending_mult_nmm": invalid_value}

    summary = build_external_validation_summary((row,), strict_mode=True)

    assert summary.status != "pass"
    assert summary.invalid_numeric_values_count == 1
    assert "invalid numeric values" in " ".join(summary.warnings)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("bending_delta_percent", float("nan")),
        ("shear_delta_percent", float("inf")),
        ("mcrc_delta_percent", -1.0),
        ("crack_width_delta_mm", float("nan")),
        ("deflection_delta_mm", -1.0),
    ),
)
def test_external_validation_tolerance_rejects_non_finite_or_negative_values(
    field_name,
    invalid_value,
):
    with pytest.raises(ValueError, match=rf"{field_name} must be finite and non-negative"):
        ExternalValidationTolerance(**{field_name: invalid_value})


def test_external_validation_tolerance_cannot_self_approve():
    with pytest.raises(ValueError, match="cannot be self-approved"):
        ExternalValidationTolerance(approved_for_acceptance=True)


def test_external_validation_tolerance_status_cannot_be_spoofed():
    with pytest.raises(ValueError, match="approval_status must remain 'ASSUMPTION'"):
        ExternalValidationTolerance(approval_status="CONFIRMED")


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "message"),
    (
        ("local_axes_id", "", "missing provenance fields: local_axes_id"),
        ("source_type", "", "missing provenance fields: source_type"),
        ("moment_axis", "global_y", "moment_axis must be 'local_z'"),
        ("load_duration", "long", "load_duration must be 'short'"),
        ("project_use", "true", "project_use must be false"),
        (
            "adapter_approval_status",
            "approved",
            "adapter_approval_status must remain 'not_approved'",
        ),
    ),
)
def test_external_validation_loader_rejects_invalid_provenance(
    tmp_path,
    field_name,
    invalid_value,
    message,
):
    csv_path = tmp_path / f"invalid_{field_name}.csv"
    _write_external_rows(
        csv_path,
        [{**_accepted_row(), field_name: invalid_value}],
    )

    with pytest.raises(ValueError, match=message):
        load_external_validation_csv(csv_path)


def test_external_validation_summary_fails_for_failed_rows():
    row = {**_accepted_row(), "acceptance_status": "failed"}
    summary = build_external_validation_summary((row,))

    assert summary.status == "fail"
    assert summary.failed_cases == 1
    assert "external validation contains failed comparison rows" in summary.warnings


def test_external_validation_summary_requires_review_when_delta_exceeds_tolerance():
    row = {**_accepted_row(), "external_mcrc_nmm": "20000000"}
    summary = build_external_validation_summary((row,))

    assert summary.status == "review_required"
    assert summary.max_mcrc_delta_percent == pytest.approx(3.225806451612903)
    assert "external validation delta exceeds draft tolerance" in summary.warnings


def test_external_validation_explicit_delta_mismatch_fails_closed():
    row = {
        **_accepted_row(),
        "external_bending_mult_nmm": "400000000",
        "delta_bending_percent": "0",
    }

    summary = build_external_validation_summary((row,), strict_mode=True)

    assert summary.status == "fail"
    assert summary.explicit_delta_mismatch_count == 1
    assert summary.max_bending_delta_percent == 100.0


def test_external_validation_duplicate_case_id_fails_closed(tmp_path):
    csv_path = tmp_path / "duplicate.csv"
    _write_external_rows(csv_path, [_accepted_row(), _accepted_row()])

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_external_validation_csv(csv_path)

    summary = build_external_validation_summary((_accepted_row(), _accepted_row()))
    assert summary.status == "fail"
    assert summary.duplicate_case_id_count == 1


def test_external_validation_strict_fails_when_delta_exceeds_tolerance():
    row = {**_accepted_row(), "external_mcrc_nmm": "20000000"}
    summary = build_external_validation_summary((row,), strict_mode=True)

    assert summary.status == "fail"
    assert summary.tolerance_failed_count == 1
    assert summary.inconsistent_acceptance_status_count == 1


def test_external_validation_strict_detects_inconsistent_acceptance_status():
    row = {**_accepted_row(), "acceptance_status": "failed"}
    summary = build_external_validation_summary((row,), strict_mode=True)

    assert summary.status == "fail"
    assert summary.failed_cases == 1
    assert summary.inconsistent_acceptance_status_count == 1
    assert "acceptance_status is inconsistent" in " ".join(summary.warnings)


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
    assert data["status"] == "review_required"
    assert data["summary"]["total_cases"] == 1
    assert data["summary"]["accepted_cases"] == 1


def test_cli_external_validation_strict_json_output(capsys):
    exit_code = main(["external-validation", "--csv", str(SAMPLE_PATH), "--strict", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "external-validation"
    assert data["strict"] is True
    assert data["status"] == "review_required"
    assert data["summary"]["strict_mode"] is True
    assert data["summary"]["tolerance_failed_count"] == 0
    assert data["summary"]["inconsistent_acceptance_status_count"] == 0


def test_cli_external_validation_strict_missing_values_review_required(tmp_path, capsys):
    csv_path = tmp_path / "missing_external.csv"
    _write_external_rows(csv_path, [_row_with_missing_external_values()])

    exit_code = main(["external-validation", "--csv", str(csv_path), "--strict", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["status"] == "review_required"
    assert data["summary"]["missing_required_external_values_count"] == 1


def test_cli_external_validation_strict_tolerance_failure(tmp_path, capsys):
    csv_path = tmp_path / "tolerance_fail.csv"
    _write_external_rows(
        csv_path,
        [{**_accepted_row(), "external_mcrc_nmm": "20000000"}],
    )

    exit_code = main(["external-validation", "--csv", str(csv_path), "--strict", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 1
    assert data["status"] == "fail"
    assert data["summary"]["tolerance_failed_count"] == 1


def test_external_validation_filled_sample_exists_with_six_cases():
    assert FILLED_SAMPLE_PATH.exists()
    with FILLED_SAMPLE_PATH.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) >= 6
    assert {row["case_id"] for row in rows} >= {
        "manual_case_01",
        "manual_case_02",
        "manual_case_03",
        "manual_case_04",
        "manual_case_05",
        "manual_case_06",
    }
    assert all(row["source_type"] == "synthetic_manual" for row in rows)
    assert all(row["acceptance_status"] == "accepted" for row in rows)


def test_cli_external_validation_sample_json_output(capsys):
    exit_code = main(["external-validation", "--sample", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    tolerances = ExternalValidationTolerance()
    summary = data["summary"]
    assert exit_code == 0
    assert data["command"] == "external-validation"
    assert data["sample"] is True
    assert data["status"] == "review_required"
    assert summary["total_cases"] == 6
    assert summary["accepted_cases"] == 6
    assert summary["review_cases"] == 0
    assert summary["failed_cases"] == 0
    assert summary["max_bending_delta_percent"] <= tolerances.bending_delta_percent
    assert summary["max_shear_delta_percent"] <= tolerances.shear_delta_percent
    assert summary["max_mcrc_delta_percent"] <= tolerances.mcrc_delta_percent
    assert summary["max_crack_width_delta_mm"] <= tolerances.crack_width_delta_mm
    assert summary["max_deflection_delta_mm"] <= tolerances.deflection_delta_mm


def _write_external_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=EXTERNAL_VALIDATION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row_with_missing_external_values() -> dict[str, str]:
    row = _accepted_row()
    row["external_bending_mult_nmm"] = ""
    row["acceptance_status"] = "review_required"
    return row


def _accepted_row() -> dict[str, str]:
    return {
        "case_id": "external_case_01",
        "source_type": "manual",
        "source_program": "independent-manual",
        "source_program_version": "1.0",
        "source_model_id": "manual-model-01",
        "source_element_id": "beam-01",
        "source_station": "midspan",
        "source_combination_id": "LC-01",
        "source_signed_action_vector": "M=150000000;Q=80000",
        "source_units": "N;Nmm;mm",
        "source_basis": "independent-manual-record",
        "transform_matrix_reference": "identity",
        "adapter_id": "manual-canonical",
        "adapter_version": "1.0",
        "adapter_approval_status": "not_approved",
        "element_type": "rectangular_beam",
        "b_mm": "300",
        "h_mm": "500",
        "cover_mm": "32",
        "concrete_class": "B25",
        "main_rebar_class": "A500",
        "stirrup_rebar_class": "A240",
        "local_axes_id": "external-case-01-local-axes",
        "moment_axis": "local_z",
        "tension_face": "local_y_min",
        "load_duration": "short",
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
        "external_deflection_mm": "18.51",
        "program_strength_status": "pass",
        "external_strength_status": "pass",
        "program_serviceability_status": "pass",
        "external_serviceability_status": "pass",
        "program_overall_status": "pass",
        "external_overall_status": "pass",
        "delta_bending_percent": "",
        "delta_shear_percent": "",
        "delta_mcrc_percent": "",
        "delta_crack_width_mm": "",
        "delta_deflection_mm": "",
        "acceptance_status": "accepted",
        "engineer_comment": "synthetic public fixture",
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": "false",
        "requires_engineer_review": "true",
    }
