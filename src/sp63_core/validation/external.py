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


def load_external_comparison_csv(path: str | Path) -> tuple[ExternalComparisonRow, ...]:
    """Load a filled external comparison CSV exported by this package."""
    input_path = Path(path)
    fieldnames = [field.name for field in fields(ExternalComparisonRow)]
    with input_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("external comparison CSV is missing header")
        missing_columns = [
            fieldname for fieldname in fieldnames if fieldname not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "external comparison CSV is missing columns: " + ", ".join(missing_columns)
            )
        return tuple(_row_from_csv(row) for row in reader)


def external_row_has_completed_source(
    row: ExternalComparisonRow,
    *,
    source: str = "any",
) -> bool:
    """Return whether the requested external source values are fully filled."""
    scad_completed = (
        row.scad_As is not None and row.scad_Mult is not None and row.scad_Qult is not None
    )
    lira_completed = (
        row.lira_As is not None and row.lira_Mult is not None and row.lira_Qult is not None
    )
    if source == "scad":
        return scad_completed
    if source == "lira":
        return lira_completed
    if source == "any":
        return scad_completed or lira_completed
    if source == "both":
        return scad_completed and lira_completed
    raise ValueError("source must be one of: any, scad, lira, both")


def evaluate_acceptance_gates(
    *,
    golden_results: Sequence[GoldenCaseResult],
    dataset_validation: DatasetValidationResult,
    external_rows: Sequence[ExternalComparisonRow] = (),
    max_delta_percent: float = 5.0,
    required_external_source: str = "any",
    require_engineer_accepted: bool = True,
) -> dict[str, Any]:
    """Evaluate draft acceptance gates before baseline ML."""
    warnings: list[str] = []
    golden_passed = all(result.passed for result in golden_results)
    dataset_passed = dataset_validation.status == "pass"
    total_external_rows = len(external_rows)
    rows_with_deltas = tuple(compute_external_deltas(row) for row in external_rows)
    completed_external_rows = sum(
        1
        for row in rows_with_deltas
        if external_row_has_completed_source(row, source=required_external_source)
    )
    external_incomplete_count = total_external_rows - completed_external_rows
    external_rejected_count = (
        sum(1 for row in rows_with_deltas if row.accepted is not True)
        if require_engineer_accepted
        else 0
    )
    external_delta_exceeded_count = sum(
        1
        for row in rows_with_deltas
        if not _row_deltas_within_limit(row, max_delta_percent)
    )
    external_completed = total_external_rows > 0 and external_incomplete_count == 0
    external_accepted = False

    if not golden_passed:
        warnings.append("golden validation failed")
    if not dataset_passed:
        warnings.append("dataset validation failed")

    if not external_rows:
        warnings.append("external SCAD/LIRA comparison is not filled yet")
        status = "fail" if not golden_passed or not dataset_passed else "warning"
    else:
        if external_incomplete_count:
            warnings.append("external comparison rows are incomplete")
        if external_rejected_count:
            warnings.append("not all external comparison rows are accepted by engineer")
        if external_delta_exceeded_count:
            warnings.append("external comparison delta exceeds acceptance limit")
        external_accepted = (
            external_incomplete_count == 0
            and external_rejected_count == 0
            and external_delta_exceeded_count == 0
        )
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
        "required_external_source": required_external_source,
        "completed_external_rows": completed_external_rows,
        "total_external_rows": total_external_rows,
        "external_incomplete_count": external_incomplete_count,
        "external_rejected_count": external_rejected_count,
        "external_delta_exceeded_count": external_delta_exceeded_count,
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


def export_external_comparison_with_deltas_csv(
    rows: Sequence[ExternalComparisonRow],
    path: str | Path,
) -> Path:
    """Export external comparison rows with delta fields computed."""
    rows_with_deltas = tuple(compute_external_deltas(row) for row in rows)
    return export_external_comparison_csv(rows_with_deltas, path)


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


def _row_from_csv(row: Mapping[str, str]) -> ExternalComparisonRow:
    return ExternalComparisonRow(
        case_id=row["case_id"],
        b=_parse_required_float(row["b"], "b"),
        h=_parse_required_float(row["h"], "h"),
        concrete_class=row["concrete_class"],
        rebar_class=row["rebar_class"],
        M=_parse_required_float(row["M"], "M"),
        Q=_parse_required_float(row["Q"], "Q"),
        program_As=_parse_required_float(row["program_As"], "program_As"),
        program_stirrups=row["program_stirrups"],
        program_Mult=_parse_required_float(row["program_Mult"], "program_Mult"),
        program_Qult=_parse_required_float(row["program_Qult"], "program_Qult"),
        scad_As=_parse_optional_float(row["scad_As"], "scad_As"),
        scad_Mult=_parse_optional_float(row["scad_Mult"], "scad_Mult"),
        scad_Qult=_parse_optional_float(row["scad_Qult"], "scad_Qult"),
        lira_As=_parse_optional_float(row["lira_As"], "lira_As"),
        lira_Mult=_parse_optional_float(row["lira_Mult"], "lira_Mult"),
        lira_Qult=_parse_optional_float(row["lira_Qult"], "lira_Qult"),
        delta_As_percent_scad=_parse_optional_float(
            row["delta_As_percent_scad"], "delta_As_percent_scad"
        ),
        delta_Mult_percent_scad=_parse_optional_float(
            row["delta_Mult_percent_scad"], "delta_Mult_percent_scad"
        ),
        delta_Qult_percent_scad=_parse_optional_float(
            row["delta_Qult_percent_scad"], "delta_Qult_percent_scad"
        ),
        delta_As_percent_lira=_parse_optional_float(
            row["delta_As_percent_lira"], "delta_As_percent_lira"
        ),
        delta_Mult_percent_lira=_parse_optional_float(
            row["delta_Mult_percent_lira"], "delta_Mult_percent_lira"
        ),
        delta_Qult_percent_lira=_parse_optional_float(
            row["delta_Qult_percent_lira"], "delta_Qult_percent_lira"
        ),
        engineer_comment=row["engineer_comment"],
        accepted=_parse_optional_bool(row["accepted"]),
    )


def _parse_required_float(value: str, field_name: str) -> float:
    parsed = _parse_optional_float(value, field_name)
    if parsed is None:
        raise ValueError(f"{field_name} must be filled")
    return parsed


def _parse_optional_float(value: str, field_name: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def _parse_optional_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized == "":
        return None
    if normalized in ("true", "1", "yes", "да"):
        return True
    if normalized in ("false", "0", "no", "нет"):
        return False
    raise ValueError(f"accepted value {value!r} is not supported")
