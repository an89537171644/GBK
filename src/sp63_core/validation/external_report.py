"""External validation summary report for engineer-filled comparison cases."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

EXTERNAL_VALIDATION_COLUMNS: tuple[str, ...] = (
    "case_id",
    "source_type",
    "element_type",
    "b_mm",
    "h_mm",
    "cover_mm",
    "concrete_class",
    "main_rebar_class",
    "stirrup_rebar_class",
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


@dataclass(frozen=True)
class ExternalValidationTolerance:
    """Draft external validation acceptance tolerances."""

    bending_delta_percent: float = 1.0
    shear_delta_percent: float = 1.0
    mcrc_delta_percent: float = 1.0
    crack_width_delta_mm: float = 0.005
    deflection_delta_mm: float = 0.05


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
    max_bending_delta_percent: float | None
    max_shear_delta_percent: float | None
    max_mcrc_delta_percent: float | None
    max_crack_width_delta_mm: float | None
    max_deflection_delta_mm: float | None
    status: str
    warnings: tuple[str, ...]
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
    inconsistent_acceptance_status_count = 0
    tolerance_failed_count = 0

    bending_deltas: list[float] = []
    shear_deltas: list[float] = []
    mcrc_deltas: list[float] = []
    crack_width_deltas: list[float] = []
    deflection_deltas: list[float] = []

    for row in rows_tuple:
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

        bending_delta = _delta_or_computed(
            row,
            delta_key="delta_bending_percent",
            program_key="program_bending_mult_nmm",
            external_key="external_bending_mult_nmm",
        )
        shear_delta = _delta_or_computed(
            row,
            delta_key="delta_shear_percent",
            program_key="program_shear_qult_n",
            external_key="external_shear_qult_n",
        )
        mcrc_delta = _delta_or_computed(
            row,
            delta_key="delta_mcrc_percent",
            program_key="program_mcrc_nmm",
            external_key="external_mcrc_nmm",
        )
        crack_width_delta = _optional_float(row.get("delta_crack_width_mm"))
        deflection_delta = _optional_float(row.get("delta_deflection_mm"))

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
            tolerance_failed=row_tolerance_failed,
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
    if inconsistent_acceptance_status_count:
        warnings.append("external validation acceptance_status is inconsistent with strict checks")

    status = _summary_status(
        strict_mode=strict_mode,
        total_cases=total_cases,
        failed_cases=failed_cases,
        review_cases=review_cases,
        missing_external_values_count=missing_external_values_count,
        invalid_numeric_values_count=invalid_numeric_values_count,
        inconsistent_acceptance_status_count=inconsistent_acceptance_status_count,
        tolerance_failed_count=tolerance_failed_count,
    )

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
        max_bending_delta_percent=_max_or_none(bending_deltas),
        max_shear_delta_percent=_max_or_none(shear_deltas),
        max_mcrc_delta_percent=_max_or_none(mcrc_deltas),
        max_crack_width_delta_mm=_max_or_none(crack_width_deltas),
        max_deflection_delta_mm=_max_or_none(deflection_deltas),
        status=status,
        warnings=tuple(warnings),
    )


def _row_has_missing_external_values(row: Mapping[str, Any]) -> bool:
    return any(_is_blank(row.get(column)) for column in EXTERNAL_RESULT_COLUMNS)


def _normalized_status(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in ("accepted", "accept", "pass", "passed"):
        return "accepted"
    if normalized in ("failed", "fail", "rejected", "reject"):
        return "failed"
    return "review"


def _delta_or_computed(
    row: Mapping[str, Any],
    *,
    delta_key: str,
    program_key: str,
    external_key: str,
) -> float | None:
    explicit_delta = _optional_float(row.get(delta_key))
    if explicit_delta is not None:
        return explicit_delta

    program_value = _optional_float(row.get(program_key))
    external_value = _optional_float(row.get(external_key))
    if program_value is None or external_value is None or program_value == 0:
        return None
    return abs(external_value - program_value) / abs(program_value) * 100.0


def _optional_float(value: Any) -> float | None:
    if _is_blank(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _max_or_none(values: list[float]) -> float | None:
    return max(values) if values else None


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
    tolerance_failed: bool,
) -> bool:
    if status == "accepted":
        return has_missing_values or has_invalid_numeric_values or tolerance_failed
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
    inconsistent_acceptance_status_count: int,
    tolerance_failed_count: int,
) -> str:
    if strict_mode:
        if tolerance_failed_count or failed_cases:
            return "fail"
        if (
            total_cases == 0
            or review_cases
            or missing_external_values_count
            or invalid_numeric_values_count
            or inconsistent_acceptance_status_count
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
