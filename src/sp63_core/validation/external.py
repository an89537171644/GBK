"""External engineering validation helpers for SCAD/LIRA comparison."""

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any

from sp63_core.dataset import DatasetCase
from sp63_core.validation.dataset_checks import DatasetValidationResult
from sp63_core.validation.golden import GoldenCaseResult


@dataclass(frozen=True)
class ExternalComparisonRow:
    """One row for manual comparison with external engineering software."""

    case_id: str
    b: float
    h: float
    concrete_class: str
    rebar_class: str
    M: float
    Q: float
    program_As: float
    program_stirrups: str
    program_Mult: float
    program_Qult: float
    scad_As: float | None = None
    scad_Mult: float | None = None
    scad_Qult: float | None = None
    lira_As: float | None = None
    lira_Mult: float | None = None
    lira_Qult: float | None = None
    delta_As_percent_scad: float | None = None
    delta_Mult_percent_scad: float | None = None
    delta_Qult_percent_scad: float | None = None
    delta_As_percent_lira: float | None = None
    delta_Mult_percent_lira: float | None = None
    delta_Qult_percent_lira: float | None = None
    engineer_comment: str = ""
    accepted: bool | None = None


def build_external_comparison_rows(
    cases: Sequence[DatasetCase],
    *,
    limit: int = 10,
) -> tuple[ExternalComparisonRow, ...]:
    """Build blank external comparison rows from dataset program outputs."""
    if limit <= 0:
        raise ValueError("limit must be positive")

    return tuple(
        ExternalComparisonRow(
            case_id=case.case_id,
            b=case.b,
            h=case.h,
            concrete_class=case.concrete_class,
            rebar_class=case.rebar_class,
            M=case.M,
            Q=case.Q,
            program_As=case.As_provided,
            program_stirrups=case.stirrup_scheme,
            program_Mult=case.Mult,
            program_Qult=case.Qult,
        )
        for case in cases[:limit]
    )


def compute_external_deltas(row: ExternalComparisonRow) -> ExternalComparisonRow:
    """Return row with SCAD/LIRA percentage deltas filled where possible."""
    return replace(
        row,
        delta_As_percent_scad=_delta_percent(row.scad_As, row.program_As),
        delta_Mult_percent_scad=_delta_percent(row.scad_Mult, row.program_Mult),
        delta_Qult_percent_scad=_delta_percent(row.scad_Qult, row.program_Qult),
        delta_As_percent_lira=_delta_percent(row.lira_As, row.program_As),
        delta_Mult_percent_lira=_delta_percent(row.lira_Mult, row.program_Mult),
        delta_Qult_percent_lira=_delta_percent(row.lira_Qult, row.program_Qult),
    )


def evaluate_acceptance_gates(
    *,
    golden_results: Sequence[GoldenCaseResult],
    dataset_validation: DatasetValidationResult,
    external_rows: Sequence[ExternalComparisonRow] = (),
    max_delta_percent: float = 5.0,
) -> dict[str, Any]:
    """Evaluate draft acceptance gates before baseline ML."""
    warnings: list[str] = []
    golden_passed = all(result.passed for result in golden_results)
    dataset_passed = dataset_validation.status == "pass"
    external_completed = bool(external_rows)
    external_accepted = False

    if not golden_passed:
        warnings.append("golden validation failed")
    if not dataset_passed:
        warnings.append("dataset validation failed")

    if not external_rows:
        warnings.append("external SCAD/LIRA comparison is not filled yet")
        status = "fail" if not golden_passed or not dataset_passed else "warning"
    else:
        rows_with_deltas = tuple(compute_external_deltas(row) for row in external_rows)
        all_rows_accepted = all(row.accepted is True for row in rows_with_deltas)
        all_deltas_accepted = all(
            _row_deltas_within_limit(row, max_delta_percent) for row in rows_with_deltas
        )
        external_accepted = all_rows_accepted and all_deltas_accepted
        if not all_rows_accepted:
            warnings.append("not all external comparison rows are accepted by engineer")
        if not all_deltas_accepted:
            warnings.append("external comparison delta exceeds acceptance limit")
        status = (
            "pass"
            if golden_passed and dataset_passed and external_accepted
            else "fail"
        )

    return {
        "status": status,
        "golden_passed": golden_passed,
        "dataset_passed": dataset_passed,
        "external_completed": external_completed,
        "external_accepted": external_accepted,
        "max_delta_percent": max_delta_percent,
        "warnings": tuple(warnings),
    }


def export_external_comparison_csv(
    rows: Sequence[ExternalComparisonRow],
    path: str | Path,
) -> Path:
    """Export external comparison rows to CSV for manual filling."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [field.name for field in fields(ExternalComparisonRow)]
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            raw_row = asdict(row)
            writer.writerow({key: _csv_value(value) for key, value in raw_row.items()})
    return output_path


def export_acceptance_report_json(report: Mapping[str, Any], path: str | Path) -> Path:
    """Export acceptance report JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dict(report), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def _delta_percent(external_value: float | None, program_value: float) -> float | None:
    if external_value is None or program_value == 0:
        return None
    return abs(external_value - program_value) / abs(program_value) * 100.0


def _row_deltas_within_limit(row: ExternalComparisonRow, max_delta_percent: float) -> bool:
    deltas = (
        row.delta_As_percent_scad,
        row.delta_Mult_percent_scad,
        row.delta_Qult_percent_scad,
        row.delta_As_percent_lira,
        row.delta_Mult_percent_lira,
        row.delta_Qult_percent_lira,
    )
    return all(delta is None or delta <= max_delta_percent for delta in deltas)


def _csv_value(value: Any) -> Any:
    return "" if value is None else value
