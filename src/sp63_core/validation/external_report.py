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

EXTERNAL_VALUES_REQUIRED_WARNING = "external validation values must be filled by an engineer"


@dataclass(frozen=True)
class ExternalValidationSummary:
    """Summary of engineer-filled external validation comparison rows."""

    total_cases: int
    accepted_cases: int
    review_cases: int
    failed_cases: int
    missing_external_values_count: int
    max_bending_delta_percent: float | None
    max_shear_delta_percent: float | None
    max_crack_width_delta_mm: float | None
    max_deflection_delta_mm: float | None
    status: str
    warnings: tuple[str, ...]
    requires_engineer_review: bool = True


def build_external_validation_summary(
    rows: Iterable[Mapping[str, Any]],
) -> ExternalValidationSummary:
    """Build a compact status summary for external validation rows."""
    rows_tuple = tuple(rows)
    total_cases = len(rows_tuple)
    accepted_cases = 0
    review_cases = 0
    failed_cases = 0
    missing_external_values_count = 0

    bending_deltas: list[float] = []
    shear_deltas: list[float] = []
    crack_width_deltas: list[float] = []
    deflection_deltas: list[float] = []

    for row in rows_tuple:
        if _row_has_missing_external_values(row):
            missing_external_values_count += 1

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
        crack_width_delta = _optional_float(row.get("delta_crack_width_mm"))
        deflection_delta = _optional_float(row.get("delta_deflection_mm"))

        if bending_delta is not None:
            bending_deltas.append(abs(bending_delta))
        if shear_delta is not None:
            shear_deltas.append(abs(shear_delta))
        if crack_width_delta is not None:
            crack_width_deltas.append(abs(crack_width_delta))
        if deflection_delta is not None:
            deflection_deltas.append(abs(deflection_delta))

    warnings: list[str] = []
    if total_cases == 0:
        warnings.append("external validation case rows are not provided")
    if missing_external_values_count:
        warnings.append(EXTERNAL_VALUES_REQUIRED_WARNING)
    if review_cases:
        warnings.append("external validation contains rows pending engineer review")
    if failed_cases:
        warnings.append("external validation contains failed comparison rows")

    if failed_cases:
        status = "fail"
    elif missing_external_values_count or review_cases or total_cases == 0:
        status = "review_required"
    else:
        status = "pass"

    return ExternalValidationSummary(
        total_cases=total_cases,
        accepted_cases=accepted_cases,
        review_cases=review_cases,
        failed_cases=failed_cases,
        missing_external_values_count=missing_external_values_count,
        max_bending_delta_percent=_max_or_none(bending_deltas),
        max_shear_delta_percent=_max_or_none(shear_deltas),
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
