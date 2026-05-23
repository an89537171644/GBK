import json

import pytest

from sp63_core.dataset import generate_dataset_cases
from sp63_core.validation import (
    ExternalComparisonRow,
    build_external_comparison_rows,
    compute_external_deltas,
    evaluate_acceptance_gates,
)
from sp63_core.validation.dataset_checks import DatasetValidationResult
from sp63_core.validation.golden import GoldenCaseResult


def test_build_external_comparison_rows_returns_program_fields():
    cases = generate_dataset_cases(limit=3)

    rows = build_external_comparison_rows(cases, limit=2)

    assert len(rows) == 2
    assert rows[0].program_As == cases[0].As_provided
    assert rows[0].program_stirrups == cases[0].stirrup_scheme
    assert rows[0].program_Mult == cases[0].Mult
    assert rows[0].program_Qult == cases[0].Qult
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


def test_evaluate_acceptance_gates_warns_when_external_rows_empty():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
    )

    assert report["status"] == "warning"
    assert report["external_completed"] is False
    assert "external SCAD/LIRA comparison is not filled yet" in report["warnings"]


def test_evaluate_acceptance_gates_passes_with_accepted_external_rows():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(_accepted_external_row(scad_As=101.0, lira_As=102.0),),
        max_delta_percent=5.0,
    )

    assert report["status"] == "pass"
    assert report["external_completed"] is True
    assert report["external_accepted"] is True
    assert report["warnings"] == ()


def test_evaluate_acceptance_gates_fails_when_external_delta_exceeds_limit():
    report = evaluate_acceptance_gates(
        golden_results=_passing_golden_results(),
        dataset_validation=_passing_dataset_validation(),
        external_rows=(_accepted_external_row(scad_As=110.0),),
        max_delta_percent=5.0,
    )

    assert report["status"] == "fail"
    assert report["external_accepted"] is False
    assert "external comparison delta exceeds acceptance limit" in report["warnings"]


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
        M=150_000_000,
        Q=80_000,
        program_As=100.0,
        program_stirrups="D8/200, 2 legs",
        program_Mult=100.0,
        program_Qult=100.0,
        scad_As=scad_As,
        scad_Mult=scad_Mult,
        scad_Qult=scad_Qult,
        lira_As=lira_As,
        lira_Mult=lira_Mult,
        lira_Qult=lira_Qult,
        accepted=True,
    )
