"""External-validation awareness for advisory ML readiness.

This module does not train ML models and does not approve ML for project use.
It summarizes whether report-derived ML datasets are backed only by synthetic
data or also have external validation and material verification evidence.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import load_report_dataset_rows
from sp63_core.materials import (
    MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
    build_material_verification_report,
)
from sp63_core.validation import (
    EXTERNAL_VALIDATION_COLUMNS,
    build_external_validation_summary,
)

NOT_PROVIDED = "not_provided"
ACCEPTED = "accepted"
VERIFIED = "engineer_verified"


@dataclass(frozen=True)
class MLExternalValidationReadinessResult:
    """Readiness status for ML datasets with external validation awareness."""

    status: str
    readiness_status: str
    dataset_path: str | None
    external_validation_csv: str | None
    row_count: int
    external_case_count: int
    accepted_external_case_count: int
    failed_external_case_count: int
    external_match_rate: float | None
    synthetic_data_only: bool
    external_validation_present: bool
    material_verification_present: bool
    ml_ready_for_research: bool
    ml_ready_for_engineering_review: bool
    ml_ready_for_project_use: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    recommendations: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def evaluate_ml_external_validation_readiness(
    *,
    dataset_path: Path | None = None,
    external_validation_csv: Path | None = None,
    material_verification_csv: Path | None = None,
) -> MLExternalValidationReadinessResult:
    """Evaluate ML readiness with external-validation and material context."""
    warnings: list[str] = [
        "ML is not approved for project use",
        "synthetic data is not external validation",
        "all ML outputs are advisory-only and require deterministic SP63 verification",
    ]
    errors: list[str] = []
    recommendations: list[str] = []

    dataset_rows: list[dict[str, Any]] = []
    if dataset_path is None:
        warnings.append("dataset is not provided")
    else:
        try:
            dataset_rows = load_report_dataset_rows(Path(dataset_path))
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"dataset cannot be read: {exc}")

    dataset_external_counts = _status_counter(dataset_rows, "external_validation_status")
    dataset_material_counts = _status_counter(dataset_rows, "material_verification_status")
    deterministic_flags_present = _deterministic_flags_present(dataset_rows)

    if dataset_rows and not deterministic_flags_present:
        warnings.append("dataset rows do not all carry deterministic_checks_required = true")
        recommendations.append("regenerate the dataset from deterministic report archives")

    external_case_count = _count_dataset_external_cases(dataset_external_counts)
    accepted_external_case_count = dataset_external_counts.get(ACCEPTED, 0)
    failed_external_case_count = dataset_external_counts.get("failed", 0)
    external_validation_present = external_case_count > 0

    if external_validation_csv is None:
        warnings.append("external validation is not provided")
        recommendations.append("provide engineer-filled external validation CSV")
    else:
        try:
            external_rows = _load_required_csv(
                Path(external_validation_csv),
                EXTERNAL_VALIDATION_COLUMNS,
                csv_name="external validation",
            )
            external_summary = build_external_validation_summary(external_rows)
            external_case_count = external_summary.total_cases
            accepted_external_case_count = external_summary.accepted_cases
            failed_external_case_count = external_summary.failed_cases
            external_validation_present = external_summary.total_cases > 0
            warnings.extend(external_summary.warnings)
            if external_summary.status == "fail":
                errors.append("external validation summary status is fail")
            elif external_summary.status == "review_required":
                warnings.append("external validation summary requires engineer review")
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"external validation CSV cannot be read: {exc}")

    material_verification_present = _dataset_has_material_verification(dataset_material_counts)
    material_verification_pass = dataset_material_counts.get(VERIFIED, 0) > 0

    if material_verification_csv is None:
        warnings.append("material verification is not provided")
        recommendations.append("provide engineer-filled material verification CSV")
    else:
        try:
            material_rows = _load_required_csv(
                Path(material_verification_csv),
                MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
                csv_name="material verification",
            )
            material_report = build_material_verification_report(material_rows)
            material_verification_present = material_report.total_rows > 0
            material_verification_pass = material_report.status == "pass"
            warnings.extend(material_report.warnings)
            if material_report.status != "pass":
                warnings.append("material verification summary requires engineer review")
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"material verification CSV cannot be read: {exc}")

    row_count = len(dataset_rows)
    external_match_rate = (
        None
        if external_case_count == 0
        else accepted_external_case_count / external_case_count
    )
    synthetic_data_only = not external_validation_present

    if not dataset_rows and dataset_path is not None and not errors:
        errors.append("dataset contains no rows")
    if synthetic_data_only:
        warnings.append("dataset has no external validation support")
    if failed_external_case_count:
        warnings.append("external validation contains failed cases")
    if not material_verification_present:
        warnings.append("dataset has no material verification support")

    ml_ready_for_research = bool(dataset_rows) and deterministic_flags_present and not errors
    ml_ready_for_engineering_review = (
        ml_ready_for_research
        and external_validation_present
        and accepted_external_case_count > 0
        and failed_external_case_count == 0
        and material_verification_present
        and material_verification_pass
    )
    ml_ready_for_project_use = False

    if not ml_ready_for_research:
        recommendations.append("fix dataset readability and deterministic provenance first")
    if not external_validation_present:
        recommendations.append(
            "attach accepted external validation cases before engineering review"
        )
    if not material_verification_present:
        recommendations.append("attach engineer material verification before engineering review")
    if ml_ready_for_engineering_review:
        recommendations.append("continue with engineer review; ML remains advisory-only")

    readiness_status = _readiness_status(
        errors=errors,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        warnings=warnings,
    )

    return MLExternalValidationReadinessResult(
        status=readiness_status,
        readiness_status=readiness_status,
        dataset_path=None if dataset_path is None else str(Path(dataset_path)),
        external_validation_csv=(
            None if external_validation_csv is None else str(Path(external_validation_csv))
        ),
        row_count=row_count,
        external_case_count=external_case_count,
        accepted_external_case_count=accepted_external_case_count,
        failed_external_case_count=failed_external_case_count,
        external_match_rate=external_match_rate,
        synthetic_data_only=synthetic_data_only,
        external_validation_present=external_validation_present,
        material_verification_present=material_verification_present,
        ml_ready_for_research=ml_ready_for_research,
        ml_ready_for_engineering_review=ml_ready_for_engineering_review,
        ml_ready_for_project_use=ml_ready_for_project_use,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        recommendations=tuple(dict.fromkeys(recommendations)),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )


def render_ml_external_readiness_markdown(
    result: MLExternalValidationReadinessResult,
) -> str:
    """Render the readiness result as a Markdown engineering review report."""
    lines = [
        "# ML External Validation Readiness Report",
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "",
        "## Dataset summary",
        "",
        f"- status: {result.status}",
        f"- dataset_path: {result.dataset_path or '-'}",
        f"- row_count: {result.row_count}",
        f"- synthetic_data_only: {result.synthetic_data_only}",
        "",
        "## External validation summary",
        "",
        f"- external_validation_csv: {result.external_validation_csv or '-'}",
        f"- external_validation_present: {result.external_validation_present}",
        f"- external_case_count: {result.external_case_count}",
        f"- accepted_external_case_count: {result.accepted_external_case_count}",
        f"- failed_external_case_count: {result.failed_external_case_count}",
        f"- external_match_rate: {_format_optional_float(result.external_match_rate)}",
        "",
        "## Material verification summary",
        "",
        f"- material_verification_present: {result.material_verification_present}",
        "",
        "## Readiness flags",
        "",
        f"- ml_ready_for_research: {result.ml_ready_for_research}",
        f"- ml_ready_for_engineering_review: {result.ml_ready_for_engineering_review}",
        f"- ml_ready_for_project_use: {result.ml_ready_for_project_use}",
        "",
        "## Warnings",
        "",
    ]
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- none")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(
        f"- {recommendation}" for recommendation in result.recommendations
    ) if result.recommendations else lines.append("- none")
    lines.extend(["", "## Limitations", ""])
    lines.extend(
        [
            "- Synthetic data is not external validation.",
            "- ML is advisory-only and is not a design checker.",
            "- Deterministic SP63 verification remains mandatory.",
            "- Engineer review is required.",
            "- This workflow is not approved for project use.",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_required_csv(
    path: Path,
    required_columns: tuple[str, ...],
    *,
    csv_name: str,
) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_name} CSV is missing header")
        missing_columns = [
            column for column in required_columns if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                f"{csv_name} CSV is missing columns: " + ", ".join(missing_columns)
            )
        return tuple(dict(row) for row in reader)


def _status_counter(rows: list[dict[str, Any]], column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(column) or NOT_PROVIDED).strip() or NOT_PROVIDED
        counts[value] = counts.get(value, 0) + 1
    return counts


def _count_dataset_external_cases(counts: Mapping[str, int]) -> int:
    return sum(count for status, count in counts.items() if status != NOT_PROVIDED)


def _dataset_has_material_verification(counts: Mapping[str, int]) -> bool:
    return any(status != NOT_PROVIDED and count > 0 for status, count in counts.items())


def _deterministic_flags_present(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    return all(_truthy(row.get("deterministic_checks_required")) for row in rows)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _readiness_status(
    *,
    errors: list[str],
    ml_ready_for_engineering_review: bool,
    warnings: list[str],
) -> str:
    if errors:
        return "fail"
    if ml_ready_for_engineering_review and not warnings:
        return "pass"
    return "review_required"


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6g}"
