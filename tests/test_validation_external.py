import csv
import json
from dataclasses import asdict

import pytest

from sp63_core.dataset import generate_dataset_cases
from sp63_core.validation import (
    ExternalComparisonRow,
    build_external_comparison_rows,
    compute_external_deltas,
    evaluate_acceptance_gates,
    export_external_comparison_csv,
    export_external_comparison_with_deltas_csv,
    external_row_has_completed_source,
    load_external_comparison_csv,
)
from sp63_core.validation.dataset_checks import DatasetValidationResult
from sp63_core.validation.golden import GoldenCaseResult


def test_build_external_comparison_rows_returns_program_fields():
    cases = generate_dataset_cases(limit=3, load_duration="short")

    rows = build_external_comparison_rows(cases, limit=2)

    assert len(rows) == 2
    assert rows[0].program_As == cases[0].As_provided
    assert rows[0].program_stirrups == cases[0].stirrup_scheme
    assert rows[0].program_Mult == cases[0].Mult
    assert rows[0].program_Qult == cases[0].Qult
    assert rows[0].local_axes_id == cases[0].local_axes_id
    assert rows[0].moment_axis == cases[0].moment_axis
    assert rows[0].tension_face == cases[0].tension_face
    assert rows[0].load_duration == "short"
    assert rows[0].completeness_status == "incomplete"
    assert rows[0].evidence_status == "needs_engineer_review"
    assert rows[0].project_use_status == "prohibited"
    assert rows[0].project_use is False
    assert rows[0].requires_engineer_review is True
    assert rows[0].scad_As is None


def test_compute_external_deltas_calculates_percent_deltas():
    row = _accepted_external_row(
        scad_As=105.0,
        scad_Mult=98.0,
        scad_Qult=101.0,
        lira_As=102.0,
        lira_Mult=97.0,
        lira_Qult=104.0,
    )

    result = compute_external_deltas(row)

    assert result.delta_As_percent_scad == pytest.approx(5.0)
    assert result.delta_Mult_percent_scad == pytest.approx(2.0)
    assert result.delta_Qult_percent_scad == pytest.approx(1.0)
    assert result.delta_As_percent_lira == pytest.approx(2.0)
    assert result.delta_Mult_percent_lira == pytest.approx(3.0)
    assert result.delta_Qult_percent_lira == pytest.approx(4.0)


def test_load_external_comparison_csv_roundtrip(tmp_path):
    rows = build_external_comparison_rows(
        generate_dataset_cases(limit=2, load_duration="short")
    )
    path = export_external_comparison_csv(rows, tmp_path / "external.csv")

    loaded = load_external_comparison_csv(path)

    assert len(loaded) == 2
    assert loaded[0].case_id == rows[0].case_id
    assert loaded[0].program_As == rows[0].program_As
    assert loaded[0].accepted is None


def test_load_external_comparison_csv_parses_filled_values(tmp_path):
    row = _accepted_external_row(
        scad_As=101.0,
        scad_Mult=102.0,
        scad_Qult=103.0,
    )
    path = export_external_comparison_csv((row,), tmp_path / "filled.csv")

    loaded = load_external_comparison_csv(path)

    assert loaded[0].scad_As == 101.0
    assert loaded[0].scad_Mult == 102.0
    assert loaded[0].scad_Qult == 103.0
    assert loaded[0].accepted is True


def test_load_external_comparison_csv_rejects_missing_provenance_column(tmp_path):
    raw_row = asdict(_accepted_external_row())
    raw_row.pop("local_axes_id")
    path = tmp_path / "missing_provenance.csv"
    _write_raw_external_comparison_row(path, raw_row)

    with pytest.raises(ValueError, match="missing columns: local_axes_id"):
        load_external_comparison_csv(path)


def test_load_external_comparison_csv_rejects_long_duration(tmp_path):
    raw_row = {**asdict(_accepted_external_row()), "load_duration": "long"}
    path = tmp_path / "long_duration.csv"
    _write_raw_external_comparison_row(path, raw_row)

    with pytest.raises(ValueError, match="load_duration must be 'short'"):
        load_external_comparison_csv(path)


def test_external_comparison_row_rejects_unsafe_project_flag():
    raw_row = {**asdict(_accepted_external_row()), "project_use": True}

    with pytest.raises(ValueError, match="project_use must be false"):
        ExternalComparisonRow(**raw_row)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("b", float("nan")),
        ("program_Mult", float("inf")),
        ("scad_As", float("-inf")),
    ),
)
def test_external_comparison_row_rejects_non_finite_numeric_input(
    field_name,
    invalid_value,
):
    raw_row = {**asdict(_accepted_external_row()), field_name: invalid_value}

    with pytest.raises(ValueError, match=rf"{field_name} must be finite"):
        ExternalComparisonRow(**raw_row)


@pytest.mark.parametrize(
    ("field_name", "message"),
    (
        ("b", "b must be positive"),
        ("h", "h must be positive"),
        ("M", "M must be non-negative"),
        ("Q", "Q must be non-negative"),
        ("program_As", "program_As must be non-negative"),
        ("program_Mult", "program_Mult must be non-negative"),
        ("program_Qult", "program_Qult must be non-negative"),
        ("scad_As", "scad_As must be non-negative"),
    ),
)
def test_external_comparison_row_rejects_negative_numeric_input(field_name, message):
    raw_row = {**asdict(_accepted_external_row()), field_name: -1.0}

    with pytest.raises(ValueError, match=message):
        ExternalComparisonRow(**raw_row)


def test_external_row_has_completed_source():
    scad_row = _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0)
    lira_row = _accepted_external_row(lira_As=101.0, lira_Mult=102.0, lira_Qult=103.0)
    both_row = _accepted_external_row(
        scad_As=101.0,
        scad_Mult=102.0,
        scad_Qult=103.0,
        lira_As=101.0,
        lira_Mult=102.0,
        lira_Qult=103.0,
    )

    assert external_row_has_completed_source(scad_row, source="scad") is True
    assert external_row_has_completed_source(scad_row, source="any") is True
    assert external_row_has_completed_source(scad_row, source="lira") is False
    assert external_row_has_completed_source(lira_row, source="lira") is True
    assert external_row_has_completed_source(both_row, source="both") is True


def test_evaluate_acceptance_gates_warns_when_external_rows_empty():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
    )

    assert report["status"] == "review_required"
    assert report["external_completed"] is False
    assert report["total_external_rows"] == 0
    assert "external SCAD/LIRA comparison is not filled yet" in report["warnings"]


def test_evaluate_acceptance_gates_requires_review_without_policy_and_adapter():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(
            _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0),
        ),
        max_delta_percent=5.0,
    )

    assert report["status"] == "review_required"
    assert report["external_completed"] is False
    assert report["external_accepted"] is False
    assert report["completed_external_rows"] == 1
    assert report["external_incomplete_count"] == 0
    assert report["completeness_status"] == "incomplete"
    assert report["evidence_status"] == "needs_engineer_review"
    assert report["project_use_status"] == "prohibited"
    assert report["project_use"] is False
    assert report["requires_engineer_review"] is True
    assert report["adapter_provenance_incomplete_count"] == 0
    assert report["adapter_unapproved_count"] == 1
    assert report["tolerance_policy_status"] == "OPEN_QUESTION"
    assert report["source_adapter_status"] == "OPEN_QUESTION"
    assert report["external_validation_status"] == "NOT_STARTED"
    assert "diagnostic only" in " ".join(report["warnings"])


def test_evaluate_acceptance_gates_fails_for_duplicate_case_ids():
    row = _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0)

    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(row, row),
    )

    assert report["status"] == "fail"
    assert report["duplicate_case_id_count"] == 1
    assert report["external_accepted"] is False


def test_evaluate_acceptance_gates_fails_for_incomplete_adapter_provenance():
    row = _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0)
    row = ExternalComparisonRow(**{**asdict(row), "source_model_id": ""})

    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(row,),
    )

    assert report["status"] == "fail"
    assert report["adapter_provenance_incomplete_count"] == 1
    assert report["external_completed"] is False


def test_evaluate_acceptance_gates_fails_when_external_delta_exceeds_limit():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(
            _accepted_external_row(scad_As=110.0, scad_Mult=100.0, scad_Qult=100.0),
        ),
        max_delta_percent=5.0,
    )

    assert report["status"] == "fail"
    assert report["external_accepted"] is False
    assert report["external_delta_exceeded_count"] == 1
    assert "external comparison delta exceeds acceptance limit" in report["warnings"]


def test_evaluate_acceptance_gates_fails_when_external_rows_incomplete():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(_accepted_external_row(),),
    )

    assert report["status"] == "fail"
    assert report["external_incomplete_count"] == 1
    assert "external comparison rows are incomplete" in report["warnings"]


def test_evaluate_acceptance_gates_fails_when_accepted_is_missing():
    row = _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0)
    row_without_acceptance = ExternalComparisonRow(
        **{**asdict(row), "accepted": None}
    )

    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(row_without_acceptance,),
    )

    assert report["status"] == "fail"
    assert report["external_rejected_count"] == 1


def test_evaluate_acceptance_gates_scad_complete_still_requires_review():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(
            _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0),
        ),
        required_external_source="scad",
    )

    assert report["status"] == "review_required"
    assert report["external_accepted"] is False


def test_evaluate_acceptance_gates_rejects_empty_golden_evidence():
    report = evaluate_acceptance_gates(
        golden_results=(),
        dataset_validation=_passing_dataset_validation(),
    )

    assert report["status"] == "fail"
    assert report["golden_passed"] is False


@pytest.mark.parametrize("invalid_tolerance", (float("nan"), float("inf"), -1.0))
def test_evaluate_acceptance_gates_rejects_invalid_diagnostic_tolerance(
    invalid_tolerance,
):
    with pytest.raises(
        ValueError,
        match="max_delta_percent must be finite and non-negative",
    ):
        evaluate_acceptance_gates(
            golden_results=_passing_golden_results(),
            dataset_validation=_passing_dataset_validation(),
            max_delta_percent=invalid_tolerance,
        )


def test_external_comparison_row_cannot_self_approve_adapter():
    raw_row = {
        **asdict(_accepted_external_row()),
        "adapter_approval_status": "approved",
    }

    with pytest.raises(ValueError, match="verified adapter registry"):
        ExternalComparisonRow(**raw_row)


def test_export_external_comparison_with_deltas_csv(tmp_path):
    row = _accepted_external_row(scad_As=101.0, scad_Mult=102.0, scad_Qult=103.0)

    path = export_external_comparison_with_deltas_csv((row,), tmp_path / "with_deltas.csv")
    loaded = load_external_comparison_csv(path)

    assert loaded[0].delta_As_percent_scad == pytest.approx(1.0)
    assert loaded[0].delta_Mult_percent_scad == pytest.approx(2.0)
    assert loaded[0].delta_Qult_percent_scad == pytest.approx(3.0)


def test_export_acceptance_report_json_roundtrip(tmp_path):
    from sp63_core.validation import export_acceptance_report_json

    path = export_acceptance_report_json({"status": "warning"}, tmp_path / "report.json")

    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "warning"


def _passing_golden_results() -> tuple[GoldenCaseResult, ...]:
    return (
        GoldenCaseResult(
            case_id="golden",
            status="pass",
            expected={"status": "pass"},
            actual={"status": "pass"},
            tolerances={},
            passed=True,
            warnings=(),
        ),
    )


def _passing_dataset_validation() -> DatasetValidationResult:
    return DatasetValidationResult(
        total_rows=1,
        unsafe_rows_count=0,
        geometry_stirrup_mismatch_count=0,
        duplicate_case_id_count=0,
        group_leakage_count=0,
        status="pass",
        warnings=(),
    )


def _accepted_external_row(
    *,
    scad_As: float | None = None,
    scad_Mult: float | None = None,
    scad_Qult: float | None = None,
    lira_As: float | None = None,
    lira_Mult: float | None = None,
    lira_Qult: float | None = None,
) -> ExternalComparisonRow:
    return ExternalComparisonRow(
        case_id="case_000001",
        b=300,
        h=500,
        concrete_class="B25",
        rebar_class="A500",
        local_axes_id="external-case-000001-local-axes",
        moment_axis="local_z",
        tension_face="local_y_min",
        load_duration="short",
        M=150_000_000,
        Q=80_000,
        program_As=100.0,
        program_stirrups="D8/200, 2 legs",
        program_Mult=100.0,
        program_Qult=100.0,
        completeness_status="incomplete",
        evidence_status="needs_engineer_review",
        project_use_status="prohibited",
        project_use=False,
        requires_engineer_review=True,
        scad_As=scad_As,
        scad_Mult=scad_Mult,
        scad_Qult=scad_Qult,
        lira_As=lira_As,
        lira_Mult=lira_Mult,
        lira_Qult=lira_Qult,
        accepted=True,
        source_program="independent-manual",
        source_program_version="1.0",
        source_model_id="manual-model-01",
        source_element_id="beam-01",
        source_station="midspan",
        source_combination_id="LC-01",
        source_signed_action_vector="M=150000000;Q=80000",
        source_units="N;Nmm;mm",
        source_basis="independent-manual-record",
        transform_matrix_reference="identity",
        adapter_id="manual-canonical",
        adapter_version="1.0",
    )


def _write_raw_external_comparison_row(path, row: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=tuple(row))
        writer.writeheader()
        writer.writerow(row)
