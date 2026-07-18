"""External validation summary report for engineer-filled comparison cases."""

import csv
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path
from typing import Any

from sp63_core.sections import RectangularBendingOrientation

EXTERNAL_VALIDATION_COLUMNS: tuple[str, ...] = (
    "case_id",
    "source_type",
    "source_program",
    "source_program_version",
    "source_model_id",
    "source_element_id",
    "source_station",
    "source_combination_id",
    "source_signed_action_vector",
    "source_units",
    "source_basis",
    "transform_matrix_reference",
    "adapter_id",
    "adapter_version",
    "adapter_approval_status",
    "element_type",
    "b_mm",
    "h_mm",
    "cover_mm",
    "concrete_class",
    "main_rebar_class",
    "stirrup_rebar_class",
    "local_axes_id",
    "moment_axis",
    "tension_face",
    "load_duration",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
    "program_bending_mult_nmm",
    "external_bending_mult_nmm",
    "program_shear_qult_n",
    "external_shear_qult_n",
    "program_mcrc_nmm",
    "external_mcrc_nmm",
    "program_crack_width_mm",
    "external_crack_width_mm",
    "program_deflection_mm",
    "external_deflection_mm",
    "program_strength_status",
    "external_strength_status",
    "program_serviceability_status",
    "external_serviceability_status",
    "program_overall_status",
    "external_overall_status",
    "delta_bending_percent",
    "delta_shear_percent",
    "delta_mcrc_percent",
    "delta_crack_width_mm",
    "delta_deflection_mm",
    "acceptance_status",
    "engineer_comment",
    "completeness_status",
    "evidence_status",
    "project_use_status",
    "project_use",
    "requires_engineer_review",
)

EXTERNAL_PROVENANCE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "source_type",
    "source_program",
    "source_program_version",
    "source_model_id",
    "source_element_id",
    "source_station",
    "source_combination_id",
    "source_signed_action_vector",
    "source_units",
    "source_basis",
    "transform_matrix_reference",
    "adapter_id",
    "adapter_version",
    "adapter_approval_status",
    "local_axes_id",
    "moment_axis",
    "tension_face",
    "load_duration",
    "completeness_status",
    "evidence_status",
    "project_use_status",
    "project_use",
    "requires_engineer_review",
)

EXTERNAL_RESULT_COLUMNS: tuple[str, ...] = (
    "external_bending_mult_nmm",
    "external_shear_qult_n",
    "external_mcrc_nmm",
    "external_crack_width_mm",
    "external_deflection_mm",
    "external_strength_status",
    "external_serviceability_status",
    "external_overall_status",
)

EXTERNAL_NUMERIC_COLUMNS: tuple[str, ...] = (
    "b_mm",
    "h_mm",
    "cover_mm",
    "moment_nmm",
    "shear_n",
    "moment_service_nmm",
    "span_mm",
    "program_bending_mult_nmm",
    "external_bending_mult_nmm",
    "program_shear_qult_n",
    "external_shear_qult_n",
    "program_mcrc_nmm",
    "external_mcrc_nmm",
    "program_crack_width_mm",
    "external_crack_width_mm",
    "program_deflection_mm",
    "external_deflection_mm",
    "delta_bending_percent",
    "delta_shear_percent",
    "delta_mcrc_percent",
    "delta_crack_width_mm",
    "delta_deflection_mm",
)

EXTERNAL_VALUES_REQUIRED_WARNING = "external validation values must be filled by an engineer"
EXTERNAL_TOLERANCE_POLICY_WARNING = (
    "external validation tolerances are an unapproved diagnostic policy; "
    "they cannot produce an accepted gate"
)
EXTERNAL_ADAPTER_WARNING = (
    "source-specific external adapters are not approved; external validation "
    "remains NOT_STARTED"
)
EXTERNAL_ADAPTER_APPROVAL_STATUS = "not_approved"
EXTERNAL_TOLERANCE_APPROVAL_STATUS = "ASSUMPTION"
# Serialization-consistency threshold only; not an engineering acceptance tolerance.
DELTA_CONSISTENCY_ABS_TOLERANCE = 1e-5


@dataclass(frozen=True)
class ExternalValidationTolerance:
    """Unapproved diagnostic thresholds retained for regression reporting."""

    bending_delta_percent: float = 1.0
    shear_delta_percent: float = 1.0
    mcrc_delta_percent: float = 1.0
    crack_width_delta_mm: float = 0.005
    deflection_delta_mm: float = 0.05
    approval_status: str = EXTERNAL_TOLERANCE_APPROVAL_STATUS
    approved_for_acceptance: bool = False

    def __post_init__(self) -> None:
        if self.approval_status != EXTERNAL_TOLERANCE_APPROVAL_STATUS:
            raise ValueError(
                "external tolerance approval_status must remain "
                f"{EXTERNAL_TOLERANCE_APPROVAL_STATUS!r} until a verified policy "
                "registry exists"
            )
        if self.approved_for_acceptance:
            raise ValueError(
                "external tolerance policy cannot be self-approved without a "
                "verified policy registry"
            )
        values = {
            "bending_delta_percent": self.bending_delta_percent,
            "shear_delta_percent": self.shear_delta_percent,
            "mcrc_delta_percent": self.mcrc_delta_percent,
            "crack_width_delta_mm": self.crack_width_delta_mm,
            "deflection_delta_mm": self.deflection_delta_mm,
        }
        for field_name, value in values.items():
            if not isfinite(value) or value < 0:
                raise ValueError(f"{field_name} must be finite and non-negative")


@dataclass(frozen=True)
class ExternalValidationSummary:
    """Summary of engineer-filled external validation comparison rows."""

    total_cases: int
    strict_mode: bool
    accepted_cases: int
    review_cases: int
    failed_cases: int
    missing_external_values_count: int
    missing_required_external_values_count: int
    inconsistent_acceptance_status_count: int
    tolerance_failed_count: int
    invalid_numeric_values_count: int
    invalid_provenance_count: int
    duplicate_case_id_count: int
    explicit_delta_mismatch_count: int
    delta_computation_failed_count: int
    max_bending_delta_percent: float | None
    max_shear_delta_percent: float | None
    max_mcrc_delta_percent: float | None
    max_crack_width_delta_mm: float | None
    max_deflection_delta_mm: float | None
    status: str
    warnings: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    tolerance_policy_status: str = EXTERNAL_TOLERANCE_APPROVAL_STATUS
    source_adapter_status: str = "OPEN_QUESTION"
    external_validation_status: str = "NOT_STARTED"
    requires_engineer_review: bool = True


def build_external_validation_summary(
    rows: Iterable[Mapping[str, Any]],
    *,
    tolerances: ExternalValidationTolerance | None = None,
    strict_mode: bool = False,
) -> ExternalValidationSummary:
    """Build a compact status summary for external validation rows."""
    active_tolerances = tolerances or ExternalValidationTolerance()
    rows_tuple = tuple(rows)
    total_cases = len(rows_tuple)
    accepted_cases = 0
    review_cases = 0
    failed_cases = 0
    missing_external_values_count = 0
    invalid_numeric_values_count = 0
    invalid_provenance_count = 0
    duplicate_case_id_count = _duplicate_case_id_count(rows_tuple)
    explicit_delta_mismatch_count = 0
    delta_computation_failed_count = 0
    inconsistent_acceptance_status_count = 0
    tolerance_failed_count = 0

    bending_deltas: list[float] = []
    shear_deltas: list[float] = []
    mcrc_deltas: list[float] = []
    crack_width_deltas: list[float] = []
    deflection_deltas: list[float] = []

    for row in rows_tuple:
        row_provenance_errors = _external_provenance_errors(row)
        if row_provenance_errors:
            invalid_provenance_count += 1
        row_missing_external_values = _row_has_missing_external_values(row)
        if row_missing_external_values:
            missing_external_values_count += 1
        row_invalid_numeric_count = _invalid_numeric_values_count(row)
        invalid_numeric_values_count += row_invalid_numeric_count

        status = _normalized_status(row.get("acceptance_status", ""))
        if status == "accepted":
            accepted_cases += 1
        elif status == "failed":
            failed_cases += 1
        else:
            review_cases += 1

        bending_delta, bending_delta_mismatch = _percent_delta_from_values(
            row,
            delta_key="delta_bending_percent",
            program_key="program_bending_mult_nmm",
            external_key="external_bending_mult_nmm",
        )
        shear_delta, shear_delta_mismatch = _percent_delta_from_values(
            row,
            delta_key="delta_shear_percent",
            program_key="program_shear_qult_n",
            external_key="external_shear_qult_n",
        )
        mcrc_delta, mcrc_delta_mismatch = _percent_delta_from_values(
            row,
            delta_key="delta_mcrc_percent",
            program_key="program_mcrc_nmm",
            external_key="external_mcrc_nmm",
        )
        crack_width_delta, crack_width_delta_mismatch = _absolute_delta_from_values(
            row,
            delta_key="delta_crack_width_mm",
            program_key="program_crack_width_mm",
            external_key="external_crack_width_mm",
        )
        deflection_delta, deflection_delta_mismatch = _absolute_delta_from_values(
            row,
            delta_key="delta_deflection_mm",
            program_key="program_deflection_mm",
            external_key="external_deflection_mm",
        )
        row_delta_mismatch_count = sum(
            (
                bending_delta_mismatch,
                shear_delta_mismatch,
                mcrc_delta_mismatch,
                crack_width_delta_mismatch,
                deflection_delta_mismatch,
            )
        )
        explicit_delta_mismatch_count += row_delta_mismatch_count
        row_delta_computation_failed = any(
            value is None
            for value in (
                bending_delta,
                shear_delta,
                mcrc_delta,
                crack_width_delta,
                deflection_delta,
            )
        )
        if row_delta_computation_failed:
            delta_computation_failed_count += 1

        if bending_delta is not None:
            bending_deltas.append(abs(bending_delta))
        if shear_delta is not None:
            shear_deltas.append(abs(shear_delta))
        if mcrc_delta is not None:
            mcrc_deltas.append(abs(mcrc_delta))
        if crack_width_delta is not None:
            crack_width_deltas.append(abs(crack_width_delta))
        if deflection_delta is not None:
            deflection_deltas.append(abs(deflection_delta))

        row_tolerance_failed = _deltas_exceed_tolerances(
            bending_deltas=[] if bending_delta is None else [abs(bending_delta)],
            shear_deltas=[] if shear_delta is None else [abs(shear_delta)],
            mcrc_deltas=[] if mcrc_delta is None else [abs(mcrc_delta)],
            crack_width_deltas=[] if crack_width_delta is None else [abs(crack_width_delta)],
            deflection_deltas=[] if deflection_delta is None else [abs(deflection_delta)],
            tolerances=active_tolerances,
        )
        if row_tolerance_failed:
            tolerance_failed_count += 1
        if strict_mode and _acceptance_status_is_inconsistent(
            status=status,
            has_missing_values=row_missing_external_values,
            has_invalid_numeric_values=row_invalid_numeric_count > 0,
            has_invalid_provenance=bool(row_provenance_errors),
            tolerance_failed=(
                row_tolerance_failed
                or row_delta_mismatch_count > 0
                or row_delta_computation_failed
            ),
        ):
            inconsistent_acceptance_status_count += 1

    warnings: list[str] = []
    if total_cases == 0:
        warnings.append("external validation case rows are not provided")
    if missing_external_values_count:
        warnings.append(EXTERNAL_VALUES_REQUIRED_WARNING)
    if review_cases:
        warnings.append("external validation contains rows pending engineer review")
    if failed_cases:
        warnings.append("external validation contains failed comparison rows")
    if tolerance_failed_count:
        warnings.append("external validation delta exceeds draft tolerance")
    if invalid_numeric_values_count:
        warnings.append("external validation contains invalid numeric values")
    if invalid_provenance_count:
        warnings.append(
            "external validation contains missing, invalid, or unsupported "
            "calculation provenance"
        )
    if duplicate_case_id_count:
        warnings.append("external validation contains duplicate case_id values")
    if explicit_delta_mismatch_count:
        warnings.append(
            "external validation explicit deltas do not match deltas computed from values"
        )
    if delta_computation_failed_count:
        warnings.append("external validation deltas cannot be computed from supplied values")
    if inconsistent_acceptance_status_count:
        warnings.append("external validation acceptance_status is inconsistent with strict checks")
    warnings.extend((EXTERNAL_TOLERANCE_POLICY_WARNING, EXTERNAL_ADAPTER_WARNING))

    status = _summary_status(
        strict_mode=strict_mode,
        total_cases=total_cases,
        failed_cases=failed_cases,
        review_cases=review_cases,
        missing_external_values_count=missing_external_values_count,
        invalid_numeric_values_count=invalid_numeric_values_count,
        invalid_provenance_count=invalid_provenance_count,
        duplicate_case_id_count=duplicate_case_id_count,
        explicit_delta_mismatch_count=explicit_delta_mismatch_count,
        delta_computation_failed_count=delta_computation_failed_count,
        inconsistent_acceptance_status_count=inconsistent_acceptance_status_count,
        tolerance_failed_count=tolerance_failed_count,
    )
    if status == "pass":
        status = "review_required"

    return ExternalValidationSummary(
        total_cases=total_cases,
        strict_mode=strict_mode,
        accepted_cases=accepted_cases,
        review_cases=review_cases,
        failed_cases=failed_cases,
        missing_external_values_count=missing_external_values_count,
        missing_required_external_values_count=missing_external_values_count,
        inconsistent_acceptance_status_count=inconsistent_acceptance_status_count,
        tolerance_failed_count=tolerance_failed_count,
        invalid_numeric_values_count=invalid_numeric_values_count,
        invalid_provenance_count=invalid_provenance_count,
        duplicate_case_id_count=duplicate_case_id_count,
        explicit_delta_mismatch_count=explicit_delta_mismatch_count,
        delta_computation_failed_count=delta_computation_failed_count,
        max_bending_delta_percent=_max_or_none(bending_deltas),
        max_shear_delta_percent=_max_or_none(shear_deltas),
        max_mcrc_delta_percent=_max_or_none(mcrc_deltas),
        max_crack_width_delta_mm=_max_or_none(crack_width_deltas),
        max_deflection_delta_mm=_max_or_none(deflection_deltas),
        status=status,
        warnings=tuple(warnings),
        tolerance_policy_status=active_tolerances.approval_status,
    )


def _row_has_missing_external_values(row: Mapping[str, Any]) -> bool:
    return any(_is_blank(row.get(column)) for column in EXTERNAL_RESULT_COLUMNS)


def load_external_validation_csv(path: str | Path) -> tuple[dict[str, str], ...]:
    """Load external validation CSV and reject incomplete provenance."""
    input_path = Path(path)
    with input_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("external validation CSV is missing header")
        missing_columns = [
            column for column in EXTERNAL_VALIDATION_COLUMNS if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "external validation CSV is missing columns: "
                + ", ".join(missing_columns)
            )
        rows = tuple(dict(row) for row in reader)
    validate_external_validation_rows(rows)
    return rows


def validate_external_validation_rows(rows: Iterable[Mapping[str, Any]]) -> None:
    """Reject rows without the supported orientation, duration, and safety flags."""
    rows_tuple = tuple(rows)
    duplicate_case_id_count = _duplicate_case_id_count(rows_tuple)
    if duplicate_case_id_count:
        raise ValueError("external validation CSV contains duplicate case_id values")
    for row_number, row in enumerate(rows_tuple, start=2):
        errors = _external_provenance_errors(row)
        if errors:
            raise ValueError(
                f"external validation CSV row {row_number}: " + "; ".join(errors)
            )


def _external_provenance_errors(row: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    missing_columns = [
        column for column in EXTERNAL_PROVENANCE_COLUMNS if _is_blank(row.get(column))
    ]
    if missing_columns:
        errors.append("missing provenance fields: " + ", ".join(missing_columns))

    if not any(
        _is_blank(row.get(column))
        for column in ("local_axes_id", "moment_axis", "tension_face")
    ):
        try:
            RectangularBendingOrientation(
                local_axes_id=row["local_axes_id"],
                moment_axis=row["moment_axis"],
                tension_face=row["tension_face"],
            )
        except ValueError as exc:
            errors.append(str(exc))

    if not _is_blank(row.get("load_duration")) and row.get("load_duration") != "short":
        errors.append(
            "load_duration must be 'short' until the shear load-combination "
            "context is implemented"
        )
    expected_text_values = {
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
    }
    for field_name, expected in expected_text_values.items():
        value = row.get(field_name)
        if not _is_blank(value) and value != expected:
            errors.append(f"{field_name} must be {expected!r}")
    adapter_approval_status = row.get("adapter_approval_status")
    if (
        not _is_blank(adapter_approval_status)
        and adapter_approval_status != EXTERNAL_ADAPTER_APPROVAL_STATUS
    ):
        errors.append(
            "adapter_approval_status must remain "
            f"{EXTERNAL_ADAPTER_APPROVAL_STATUS!r} until a verified adapter registry exists"
        )
    if not _is_blank(row.get("project_use")) and _strict_bool(row.get("project_use")) is not False:
        errors.append("project_use must be false")
    if (
        not _is_blank(row.get("requires_engineer_review"))
        and _strict_bool(row.get("requires_engineer_review")) is not True
    ):
        errors.append("requires_engineer_review must be true")
    return tuple(errors)


def _strict_bool(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def _normalized_status(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in ("accepted", "accept", "pass", "passed"):
        return "accepted"
    if normalized in ("failed", "fail", "rejected", "reject"):
        return "failed"
    return "review"


def _percent_delta_from_values(
    row: Mapping[str, Any],
    *,
    delta_key: str,
    program_key: str,
    external_key: str,
) -> tuple[float | None, bool]:
    explicit_delta = _optional_float(row.get(delta_key))
    program_value = _optional_float(row.get(program_key))
    external_value = _optional_float(row.get(external_key))
    if program_value is None or external_value is None:
        computed_delta = None
    elif program_value == 0:
        computed_delta = 0.0 if external_value == 0 else None
    else:
        computed_delta = abs(external_value - program_value) / abs(program_value) * 100.0
    return computed_delta, _explicit_delta_mismatch(
        raw_explicit_delta=row.get(delta_key),
        explicit_delta=explicit_delta,
        computed_delta=computed_delta,
    )


def _absolute_delta_from_values(
    row: Mapping[str, Any],
    *,
    delta_key: str,
    program_key: str,
    external_key: str,
) -> tuple[float | None, bool]:
    explicit_delta = _optional_float(row.get(delta_key))
    program_value = _optional_float(row.get(program_key))
    external_value = _optional_float(row.get(external_key))
    computed_delta = (
        None
        if program_value is None or external_value is None
        else abs(external_value - program_value)
    )
    return computed_delta, _explicit_delta_mismatch(
        raw_explicit_delta=row.get(delta_key),
        explicit_delta=explicit_delta,
        computed_delta=computed_delta,
    )


def _explicit_delta_mismatch(
    *,
    raw_explicit_delta: Any,
    explicit_delta: float | None,
    computed_delta: float | None,
) -> bool:
    if _is_blank(raw_explicit_delta):
        return False
    if explicit_delta is None or computed_delta is None:
        return True
    return not isclose(
        explicit_delta,
        computed_delta,
        rel_tol=0.0,
        abs_tol=DELTA_CONSISTENCY_ABS_TOLERANCE,
    )


def _optional_float(value: Any) -> float | None:
    if _is_blank(value):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) and parsed >= 0 else None


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _max_or_none(values: list[float]) -> float | None:
    return max(values) if values else None


def _duplicate_case_id_count(rows: Iterable[Mapping[str, Any]]) -> int:
    counts = Counter(
        str(row.get("case_id") or "").strip()
        for row in rows
        if not _is_blank(row.get("case_id"))
    )
    return sum(count - 1 for count in counts.values() if count > 1)


def _invalid_numeric_values_count(row: Mapping[str, Any]) -> int:
    return sum(
        1
        for column in EXTERNAL_NUMERIC_COLUMNS
        if not _is_blank(row.get(column)) and _optional_float(row.get(column)) is None
    )


def _acceptance_status_is_inconsistent(
    *,
    status: str,
    has_missing_values: bool,
    has_invalid_numeric_values: bool,
    has_invalid_provenance: bool,
    tolerance_failed: bool,
) -> bool:
    if status == "accepted":
        return (
            has_missing_values
            or has_invalid_numeric_values
            or has_invalid_provenance
            or tolerance_failed
        )
    if status == "failed":
        return not tolerance_failed
    return False


def _summary_status(
    *,
    strict_mode: bool,
    total_cases: int,
    failed_cases: int,
    review_cases: int,
    missing_external_values_count: int,
    invalid_numeric_values_count: int,
    invalid_provenance_count: int,
    duplicate_case_id_count: int,
    explicit_delta_mismatch_count: int,
    delta_computation_failed_count: int,
    inconsistent_acceptance_status_count: int,
    tolerance_failed_count: int,
) -> str:
    if (
        invalid_provenance_count
        or duplicate_case_id_count
        or explicit_delta_mismatch_count
    ):
        return "fail"
    if strict_mode:
        if tolerance_failed_count or failed_cases:
            return "fail"
        if (
            total_cases == 0
            or review_cases
            or missing_external_values_count
            or invalid_numeric_values_count
            or inconsistent_acceptance_status_count
            or delta_computation_failed_count
        ):
            return "review_required"
        return "pass"

    if failed_cases:
        return "fail"
    if (
        missing_external_values_count
        or review_cases
        or total_cases == 0
        or invalid_numeric_values_count
        or tolerance_failed_count
        or delta_computation_failed_count
    ):
        return "review_required"
    return "pass"


def _deltas_exceed_tolerances(
    *,
    bending_deltas: list[float],
    shear_deltas: list[float],
    mcrc_deltas: list[float],
    crack_width_deltas: list[float],
    deflection_deltas: list[float],
    tolerances: ExternalValidationTolerance,
) -> bool:
    return (
        _exceeds(bending_deltas, tolerances.bending_delta_percent)
        or _exceeds(shear_deltas, tolerances.shear_delta_percent)
        or _exceeds(mcrc_deltas, tolerances.mcrc_delta_percent)
        or _exceeds(crack_width_deltas, tolerances.crack_width_delta_mm)
        or _exceeds(deflection_deltas, tolerances.deflection_delta_mm)
    )


def _exceeds(values: list[float], limit: float) -> bool:
    return any(value > limit for value in values)
