"""Material verification readiness for advisory ML datasets.

The checks in this module only verify whether material classes appearing in a
report-derived dataset are covered by an engineer-filled material verification
CSV. They do not change catalog values and do not approve ML for project use.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset import load_report_dataset_rows
from sp63_core.materials import (
    MATERIAL_VERIFICATION_REQUIRED_COLUMNS,
    build_material_verification_report,
)
from sp63_core.materials.audit import CONCRETE_PROPERTY_USAGE, REBAR_PROPERTY_USAGE

DATASET_CONCRETE_COLUMN = "concrete_class"
DATASET_LONGITUDINAL_REBAR_COLUMN = "longitudinal_rebar_class"
DATASET_STIRRUP_REBAR_COLUMN = "stirrup_rebar_class"
VERIFIED_STATUS = "engineer_verified"
REJECTED_STATUSES = {"rejected", "reject", "failed", "fail"}


@dataclass(frozen=True)
class MLMaterialVerificationReadinessResult:
    """Material verification coverage summary for ML/report-derived datasets."""

    status: str
    source_dataset: str
    material_verification_csv: str | None
    row_count: int
    dataset_concrete_classes: tuple[str, ...]
    dataset_longitudinal_rebar_classes: tuple[str, ...]
    dataset_stirrup_rebar_classes: tuple[str, ...]
    required_material_keys: tuple[str, ...]
    verified_material_keys: tuple[str, ...]
    missing_material_keys: tuple[str, ...]
    rejected_material_keys: tuple[str, ...]
    review_required_material_keys: tuple[str, ...]
    material_coverage_ratio: float
    material_verification_present: bool
    material_verification_complete: bool
    material_ready_for_engineering_review: bool
    material_ready_for_project_use: bool
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    synthetic_data_only: bool = True
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def evaluate_ml_material_verification_readiness(
    *,
    dataset_path: Path,
    material_verification_csv: Path | None = None,
    dataset_format: str | None = None,
) -> MLMaterialVerificationReadinessResult:
    """Evaluate material verification coverage for a report-derived dataset."""
    source_dataset = str(Path(dataset_path))
    warnings: list[str] = [
        "material verification readiness does not certify ML output or design calculations",
        "material verification does not replace external validation",
        "ML remains advisory-only and deterministic SP63 checks remain mandatory",
    ]
    errors: list[str] = []

    rows: list[dict[str, Any]] = []
    try:
        rows = load_report_dataset_rows(Path(dataset_path), dataset_format)
    except (FileNotFoundError, ValueError, OSError) as exc:
        errors.append(f"dataset cannot be read: {exc}")

    concrete_classes = _sorted_non_empty_values(rows, DATASET_CONCRETE_COLUMN)
    longitudinal_rebar_classes = _sorted_non_empty_values(
        rows,
        DATASET_LONGITUDINAL_REBAR_COLUMN,
    )
    stirrup_rebar_classes = _sorted_non_empty_values(rows, DATASET_STIRRUP_REBAR_COLUMN)
    missing_dataset_columns = _missing_dataset_material_columns(rows)
    empty_dataset_fields = _empty_dataset_material_fields(rows)
    if missing_dataset_columns:
        errors.append(
            "dataset is missing material columns: " + ", ".join(missing_dataset_columns)
        )
    if empty_dataset_fields:
        errors.append(
            "dataset contains empty material class fields: " + ", ".join(empty_dataset_fields)
        )

    required_material_keys = _required_material_keys(
        concrete_classes=concrete_classes,
        longitudinal_rebar_classes=longitudinal_rebar_classes,
        stirrup_rebar_classes=stirrup_rebar_classes,
    )
    verified_material_keys: tuple[str, ...] = ()
    missing_material_keys = required_material_keys
    rejected_material_keys: tuple[str, ...] = ()
    review_required_material_keys: tuple[str, ...] = ()
    material_verification_present = False

    if not rows and not errors:
        errors.append("dataset contains no rows")

    if material_verification_csv is None:
        warnings.append("material verification CSV is not provided")
    else:
        try:
            csv_rows = _load_material_verification_csv(Path(material_verification_csv))
            material_verification_present = True
            material_report = build_material_verification_report(csv_rows)
            warnings.extend(material_report.warnings)
            verification = _verification_status_by_material_key(csv_rows)
            verified_material_keys = _covered_keys(required_material_keys, verification, "verified")
            rejected_material_keys = _covered_keys(required_material_keys, verification, "rejected")
            missing_material_keys = tuple(
                key for key in required_material_keys if key not in verification
            )
            review_required_material_keys = tuple(
                key
                for key in required_material_keys
                if key not in verified_material_keys
                and key not in rejected_material_keys
                and key not in missing_material_keys
            )
            if material_report.invalid_rows_count:
                warnings.append("material verification CSV contains invalid rows")
            if material_report.value_mismatch_count:
                warnings.append("material verification values differ from current catalog")
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"material verification CSV cannot be read: {exc}")

    material_coverage_ratio = (
        0.0
        if not required_material_keys
        else len(verified_material_keys) / len(required_material_keys)
    )
    material_verification_complete = (
        bool(required_material_keys)
        and not missing_material_keys
        and not rejected_material_keys
        and not review_required_material_keys
    )
    material_ready_for_engineering_review = (
        material_verification_present
        and material_verification_complete
        and not rejected_material_keys
        and not errors
    )
    material_ready_for_project_use = False

    if missing_material_keys:
        warnings.append("material verification CSV is missing required dataset materials")
    if rejected_material_keys:
        warnings.append("material verification CSV rejects required dataset materials")
    if review_required_material_keys:
        warnings.append("material verification CSV has required materials needing review")

    status = _status(
        errors=errors,
        rejected_material_keys=rejected_material_keys,
        material_verification_present=material_verification_present,
        material_verification_complete=material_verification_complete,
    )

    return MLMaterialVerificationReadinessResult(
        status=status,
        source_dataset=source_dataset,
        material_verification_csv=(
            None
            if material_verification_csv is None
            else str(Path(material_verification_csv))
        ),
        row_count=len(rows),
        dataset_concrete_classes=concrete_classes,
        dataset_longitudinal_rebar_classes=longitudinal_rebar_classes,
        dataset_stirrup_rebar_classes=stirrup_rebar_classes,
        required_material_keys=required_material_keys,
        verified_material_keys=verified_material_keys,
        missing_material_keys=missing_material_keys,
        rejected_material_keys=rejected_material_keys,
        review_required_material_keys=review_required_material_keys,
        material_coverage_ratio=material_coverage_ratio,
        material_verification_present=material_verification_present,
        material_verification_complete=material_verification_complete,
        material_ready_for_engineering_review=material_ready_for_engineering_review,
        material_ready_for_project_use=material_ready_for_project_use,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(dict.fromkeys(errors)),
        synthetic_data_only=True,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )


def render_ml_material_readiness_markdown(
    result: MLMaterialVerificationReadinessResult,
) -> str:
    """Render material verification readiness as Markdown."""
    lines = [
        "# ML Material Verification Readiness - Advisory Only",
        "",
        "Material verification readiness does not certify ML output or design "
        "calculations. Deterministic SP63 verification and engineer review remain "
        "mandatory.",
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "",
        "## Dataset summary",
        "",
        f"- source_dataset: {result.source_dataset}",
        f"- row_count: {result.row_count}",
        f"- synthetic_data_only: {result.synthetic_data_only}",
        "",
        "## Required materials",
        "",
        f"- concrete classes: {_format_tuple(result.dataset_concrete_classes)}",
        "- longitudinal rebar classes: "
        + _format_tuple(result.dataset_longitudinal_rebar_classes),
        f"- stirrup rebar classes: {_format_tuple(result.dataset_stirrup_rebar_classes)}",
        f"- required material keys: {_format_tuple(result.required_material_keys)}",
        "",
        "## Verification coverage",
        "",
        f"- verified: {_format_tuple(result.verified_material_keys)}",
        f"- missing: {_format_tuple(result.missing_material_keys)}",
        f"- rejected: {_format_tuple(result.rejected_material_keys)}",
        f"- review_required: {_format_tuple(result.review_required_material_keys)}",
        f"- material_coverage_ratio: {result.material_coverage_ratio:.6g}",
        "",
        "## Readiness flags",
        "",
        f"- material_verification_present: {result.material_verification_present}",
        f"- material_verification_complete: {result.material_verification_complete}",
        "- material_ready_for_engineering_review: "
        f"{result.material_ready_for_engineering_review}",
        f"- material_ready_for_project_use: {result.material_ready_for_project_use}",
        "",
        "## Warnings",
        "",
    ]
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- none")
    lines.extend(["", "## Limitations", ""])
    lines.extend(
        [
            "- No material catalog values are changed automatically.",
            "- Material verification is not external validation.",
            "- This report does not certify the calculation core.",
            "- ML remains advisory-only.",
            "- Deterministic SP63 checks remain mandatory.",
            "- Engineer review is required.",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_material_verification_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("material verification CSV is missing header")
        missing_columns = [
            column
            for column in MATERIAL_VERIFICATION_REQUIRED_COLUMNS
            if column not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "material verification CSV is missing columns: " + ", ".join(missing_columns)
            )
        return tuple(dict(row) for row in reader)


def _required_material_keys(
    *,
    concrete_classes: tuple[str, ...],
    longitudinal_rebar_classes: tuple[str, ...],
    stirrup_rebar_classes: tuple[str, ...],
) -> tuple[str, ...]:
    keys = [
        *(f"concrete:{class_name}" for class_name in concrete_classes),
        *(f"longitudinal_rebar:{class_name}" for class_name in longitudinal_rebar_classes),
        *(f"stirrup_rebar:{class_name}" for class_name in stirrup_rebar_classes),
    ]
    return tuple(sorted(dict.fromkeys(keys)))


def _verification_status_by_material_key(
    csv_rows: tuple[Mapping[str, Any], ...],
) -> dict[str, str]:
    by_class: dict[tuple[str, str], dict[str, str]] = {}
    for row in csv_rows:
        material_type = str(row.get("material_type") or "").strip()
        class_name = str(row.get("class_name") or "").strip()
        property_name = str(row.get("property_name") or "").strip()
        if not material_type or not class_name or not property_name:
            continue
        if property_name not in _required_properties_for_material_type(material_type):
            continue
        by_class.setdefault((material_type, class_name), {})[property_name] = (
            _property_status(row)
        )

    key_status: dict[str, str] = {}
    for (material_type, class_name), property_statuses in by_class.items():
        class_status = _class_status(material_type, property_statuses)
        if material_type == "concrete":
            key_status[f"concrete:{class_name}"] = class_status
        elif material_type == "rebar":
            key_status[f"longitudinal_rebar:{class_name}"] = class_status
            key_status[f"stirrup_rebar:{class_name}"] = class_status
    return key_status


def _property_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("verification_status") or "").strip().lower()
    if status in REJECTED_STATUSES:
        return "rejected"
    if status != VERIFIED_STATUS:
        return "review_required"
    required_fields = ("engineer_value", "engineer_name", "review_date", "source_note")
    if any(_is_blank(row.get(field)) for field in required_fields):
        return "review_required"
    return "verified"


def _class_status(
    material_type: str,
    property_statuses: Mapping[str, str],
) -> str:
    required_properties = _required_properties_for_material_type(material_type)
    statuses = tuple(property_statuses.get(property_name) for property_name in required_properties)
    if any(status == "rejected" for status in statuses):
        return "rejected"
    if all(status == "verified" for status in statuses):
        return "verified"
    return "review_required"


def _required_properties_for_material_type(material_type: str) -> tuple[str, ...]:
    if material_type == "concrete":
        return tuple(CONCRETE_PROPERTY_USAGE)
    if material_type == "rebar":
        return tuple(REBAR_PROPERTY_USAGE)
    return ()


def _covered_keys(
    required_keys: tuple[str, ...],
    verification: Mapping[str, str],
    status: str,
) -> tuple[str, ...]:
    return tuple(key for key in required_keys if verification.get(key) == status)


def _missing_dataset_material_columns(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    if not rows:
        return ()
    required_columns = (
        DATASET_CONCRETE_COLUMN,
        DATASET_LONGITUDINAL_REBAR_COLUMN,
        DATASET_STIRRUP_REBAR_COLUMN,
    )
    return tuple(column for column in required_columns if any(column not in row for row in rows))


def _empty_dataset_material_fields(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    required_columns = (
        DATASET_CONCRETE_COLUMN,
        DATASET_LONGITUDINAL_REBAR_COLUMN,
        DATASET_STIRRUP_REBAR_COLUMN,
    )
    return tuple(
        column
        for column in required_columns
        if any(column in row and _is_blank(row.get(column)) for row in rows)
    )


def _sorted_non_empty_values(
    rows: Iterable[Mapping[str, Any]],
    column: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(row[column]).strip()
                for row in rows
                if column in row and not _is_blank(row.get(column))
            }
        )
    )


def _status(
    *,
    errors: list[str],
    rejected_material_keys: tuple[str, ...],
    material_verification_present: bool,
    material_verification_complete: bool,
) -> str:
    if errors or rejected_material_keys:
        return "fail"
    if not material_verification_present or not material_verification_complete:
        return "review_required"
    return "review_required"


def _format_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "-"


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""
