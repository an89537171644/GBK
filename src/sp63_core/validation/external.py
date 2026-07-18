"""External engineering validation helpers for SCAD/LIRA comparison."""

import csv
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from math import isfinite
from pathlib import Path
from typing import Any

from sp63_core.dataset import DatasetCase
from sp63_core.sections import RectangularBendingOrientation
from sp63_core.validation.dataset_checks import DatasetValidationResult
from sp63_core.validation.golden import GoldenCaseResult

EXTERNAL_TOLERANCE_POLICY_STATUS = "OPEN_QUESTION"
EXTERNAL_ADAPTER_STATUS = "not_approved"
EXTERNAL_ADAPTER_DECISION_STATUS = "OPEN_QUESTION"


@dataclass(frozen=True)
class ExternalComparisonRow:
    """One row for manual comparison with external engineering software."""

    case_id: str
    b: float
    h: float
    concrete_class: str
    rebar_class: str
    local_axes_id: str
    moment_axis: str
    tension_face: str
    load_duration: str
    M: float
    Q: float
    program_As: float
    program_stirrups: str
    program_Mult: float
    program_Qult: float
    completeness_status: str
    evidence_status: str
    project_use_status: str
    project_use: bool
    requires_engineer_review: bool
    source_program: str = ""
    source_program_version: str = ""
    source_model_id: str = ""
    source_element_id: str = ""
    source_station: str = ""
    source_combination_id: str = ""
    source_signed_action_vector: str = ""
    source_units: str = ""
    source_basis: str = ""
    transform_matrix_reference: str = ""
    adapter_id: str = ""
    adapter_version: str = ""
    adapter_approval_status: str = EXTERNAL_ADAPTER_STATUS
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

    def __post_init__(self) -> None:
        """Reject incomplete or unsupported calculation provenance."""
        RectangularBendingOrientation(
            local_axes_id=self.local_axes_id,
            moment_axis=self.moment_axis,
            tension_face=self.tension_face,
        )
        if self.load_duration != "short":
            raise ValueError(
                "external comparison load_duration must be 'short' until the "
                "shear load-combination context is implemented"
            )
        if self.completeness_status != "incomplete":
            raise ValueError(
                "external comparison completeness_status must be 'incomplete'"
            )
        if self.evidence_status != "needs_engineer_review":
            raise ValueError(
                "external comparison evidence_status must be 'needs_engineer_review'"
            )
        if self.project_use_status != "prohibited":
            raise ValueError(
                "external comparison project_use_status must be 'prohibited'"
            )
        if self.project_use is not False:
            raise ValueError("external comparison project_use must be false")
        if self.requires_engineer_review is not True:
            raise ValueError(
                "external comparison requires_engineer_review must be true"
            )
        if self.adapter_approval_status != EXTERNAL_ADAPTER_STATUS:
            raise ValueError(
                "external comparison adapter_approval_status must be "
                f"{EXTERNAL_ADAPTER_STATUS!r} until a verified adapter registry exists"
            )
        required_numeric_values = {
            "b": self.b,
            "h": self.h,
            "M": self.M,
            "Q": self.Q,
            "program_As": self.program_As,
            "program_Mult": self.program_Mult,
            "program_Qult": self.program_Qult,
        }
        optional_numeric_values = {
            "scad_As": self.scad_As,
            "scad_Mult": self.scad_Mult,
            "scad_Qult": self.scad_Qult,
            "lira_As": self.lira_As,
            "lira_Mult": self.lira_Mult,
            "lira_Qult": self.lira_Qult,
            "delta_As_percent_scad": self.delta_As_percent_scad,
            "delta_Mult_percent_scad": self.delta_Mult_percent_scad,
            "delta_Qult_percent_scad": self.delta_Qult_percent_scad,
            "delta_As_percent_lira": self.delta_As_percent_lira,
            "delta_Mult_percent_lira": self.delta_Mult_percent_lira,
            "delta_Qult_percent_lira": self.delta_Qult_percent_lira,
        }
        for field_name, value in required_numeric_values.items():
            if not isfinite(value):
                raise ValueError(f"{field_name} must be finite")
        for field_name, value in optional_numeric_values.items():
            if value is not None and not isfinite(value):
                raise ValueError(f"{field_name} must be finite when filled")
        for field_name in ("b", "h"):
            if required_numeric_values[field_name] <= 0:
                raise ValueError(f"{field_name} must be positive")
        for field_name in ("M", "Q", "program_As", "program_Mult", "program_Qult"):
            if required_numeric_values[field_name] < 0:
                raise ValueError(f"{field_name} must be non-negative")
        for field_name, value in optional_numeric_values.items():
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative when filled")


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
            local_axes_id=case.local_axes_id,
            moment_axis=case.moment_axis,
            tension_face=case.tension_face,
            load_duration=case.load_duration,
            M=case.M,
            Q=case.Q,
            program_As=case.As_provided,
            program_stirrups=case.stirrup_scheme,
            program_Mult=case.Mult,
            program_Qult=case.Qult,
            completeness_status=case.completeness_status,
            evidence_status=case.evidence_status,
            project_use_status=case.project_use_status,
            project_use=case.project_use,
            requires_engineer_review=case.requires_engineer_review,
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
        rows = tuple(_row_from_csv(row) for row in reader)
    if _duplicate_case_id_count(rows):
        raise ValueError("external comparison CSV contains duplicate case_id values")
    return rows


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
    max_delta_percent: float | None = None,
    required_external_source: str = "any",
    require_engineer_accepted: bool = True,
) -> dict[str, Any]:
    """Evaluate diagnostic gates without approving external evidence.

    ED-04 adapters and the ED-05 tolerance policy remain open engineering
    questions. Numerical deltas may be reported, but this function cannot
    produce an accepted external-validation gate in the current revision.
    """
    if max_delta_percent is not None and (
        not isfinite(max_delta_percent) or max_delta_percent < 0
    ):
        raise ValueError("max_delta_percent must be finite and non-negative")
    if required_external_source not in {"any", "scad", "lira", "both"}:
        raise ValueError("required_external_source must be one of: any, scad, lira, both")
    warnings: list[str] = []
    golden_passed = bool(golden_results) and all(
        result.passed for result in golden_results
    )
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
    external_delta_exceeded_count = (
        0
        if max_delta_percent is None
        else sum(
            1
            for row in rows_with_deltas
            if not _row_deltas_within_limit(row, max_delta_percent)
        )
    )
    adapter_provenance_incomplete_count = sum(
        1 for row in rows_with_deltas if not _adapter_provenance_complete(row)
    )
    adapter_unapproved_count = sum(
        1
        for row in rows_with_deltas
        if row.adapter_approval_status == EXTERNAL_ADAPTER_STATUS
    )
    duplicate_case_id_count = _duplicate_case_id_count(rows_with_deltas)
    external_completed = (
        total_external_rows > 0
        and external_incomplete_count == 0
        and adapter_provenance_incomplete_count == 0
        and adapter_unapproved_count == 0
        and duplicate_case_id_count == 0
    )
    external_accepted = False

    if not golden_passed:
        warnings.append("golden validation failed")
    if not dataset_passed:
        warnings.append("dataset validation failed")

    warnings.append(
        "external tolerance policy is not approved; numeric deltas are diagnostic only"
    )
    if adapter_provenance_incomplete_count:
        warnings.append("external source adapter provenance is incomplete")
    if adapter_unapproved_count:
        warnings.append("external source adapter is not approved")
    if duplicate_case_id_count:
        warnings.append("external comparison contains duplicate case_id values")

    if not external_rows:
        warnings.append("external SCAD/LIRA comparison is not filled yet")
        status = "fail" if not golden_passed or not dataset_passed else "review_required"
    else:
        if external_incomplete_count:
            warnings.append("external comparison rows are incomplete")
        if external_rejected_count:
            warnings.append("not all external comparison rows are accepted by engineer")
        if external_delta_exceeded_count:
            warnings.append("external comparison delta exceeds acceptance limit")
        blocking_failure = (
            not golden_passed
            or not dataset_passed
            or external_incomplete_count > 0
            or external_rejected_count > 0
            or external_delta_exceeded_count > 0
            or adapter_provenance_incomplete_count > 0
            or duplicate_case_id_count > 0
        )
        status = "fail" if blocking_failure else "review_required"

    return {
        "status": status,
        "golden_passed": golden_passed,
        "golden_case_count": len(golden_results),
        "golden_passed_count": sum(1 for result in golden_results if result.passed),
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
        "adapter_provenance_incomplete_count": adapter_provenance_incomplete_count,
        "adapter_unapproved_count": adapter_unapproved_count,
        "duplicate_case_id_count": duplicate_case_id_count,
        "tolerance_policy_status": EXTERNAL_TOLERANCE_POLICY_STATUS,
        "source_adapter_status": EXTERNAL_ADAPTER_DECISION_STATUS,
        "external_validation_status": "NOT_STARTED",
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
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
        local_axes_id=row["local_axes_id"],
        moment_axis=row["moment_axis"],
        tension_face=row["tension_face"],
        load_duration=row["load_duration"],
        M=_parse_required_float(row["M"], "M"),
        Q=_parse_required_float(row["Q"], "Q"),
        program_As=_parse_required_float(row["program_As"], "program_As"),
        program_stirrups=row["program_stirrups"],
        program_Mult=_parse_required_float(row["program_Mult"], "program_Mult"),
        program_Qult=_parse_required_float(row["program_Qult"], "program_Qult"),
        completeness_status=row["completeness_status"],
        evidence_status=row["evidence_status"],
        project_use_status=row["project_use_status"],
        project_use=_parse_required_bool(row["project_use"], "project_use"),
        requires_engineer_review=_parse_required_bool(
            row["requires_engineer_review"], "requires_engineer_review"
        ),
        source_program=row["source_program"],
        source_program_version=row["source_program_version"],
        source_model_id=row["source_model_id"],
        source_element_id=row["source_element_id"],
        source_station=row["source_station"],
        source_combination_id=row["source_combination_id"],
        source_signed_action_vector=row["source_signed_action_vector"],
        source_units=row["source_units"],
        source_basis=row["source_basis"],
        transform_matrix_reference=row["transform_matrix_reference"],
        adapter_id=row["adapter_id"],
        adapter_version=row["adapter_version"],
        adapter_approval_status=row["adapter_approval_status"],
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
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if not isfinite(parsed):
        raise ValueError(f"{field_name} must be finite")
    return parsed


def _parse_optional_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized == "":
        return None
    if normalized in ("true", "1", "yes", "да"):
        return True
    if normalized in ("false", "0", "no", "нет"):
        return False
    raise ValueError(f"accepted value {value!r} is not supported")


def _parse_required_bool(value: str, field_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    if normalized == "":
        raise ValueError(f"{field_name} must be filled")
    raise ValueError(f"{field_name} must be 'true' or 'false'")


def _adapter_provenance_complete(row: ExternalComparisonRow) -> bool:
    required_values = (
        row.case_id,
        row.source_program,
        row.source_program_version,
        row.source_model_id,
        row.source_element_id,
        row.source_station,
        row.source_combination_id,
        row.source_signed_action_vector,
        row.source_units,
        row.source_basis,
        row.transform_matrix_reference,
        row.adapter_id,
        row.adapter_version,
    )
    return all(value.strip() for value in required_values)


def _duplicate_case_id_count(rows: Sequence[ExternalComparisonRow]) -> int:
    counts = Counter(row.case_id.strip() for row in rows if row.case_id.strip())
    return sum(count - 1 for count in counts.values() if count > 1)
