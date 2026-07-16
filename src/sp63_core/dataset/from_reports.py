"""Export ML-ready rows from validated report archives."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sp63_core.dataset.generator import DATASET_VERSION
from sp63_core.report import validate_batch_report_archive, validate_report_bundle
from sp63_core.report.manifest import compute_file_sha256
from sp63_core.sections import RectangularBendingOrientation

REPORT_DATASET_SOURCE = "validated_report_archive"
SUPPORTED_REPORT_DATASET_FORMATS = ("jsonl", "json", "csv")


@dataclass(frozen=True)
class ReportDatasetExportResult:
    """Result of exporting dataset rows from a report archive."""

    status: str
    source_path: str
    output_path: str | None
    row_count: int
    skipped_count: int
    input_error_count: int
    archive_validation_status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True


def export_dataset_from_report_archive(
    *,
    source_path: Path,
    output_path: Path | None = None,
    output_format: str = "jsonl",
    require_archive_validation: bool = True,
) -> ReportDatasetExportResult:
    """Export flat ML-ready rows from a single or batch report archive."""
    source = Path(source_path)
    output = None if output_path is None else Path(output_path)
    output_format = output_format.lower()
    warnings: list[str] = []
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    skipped_count = 0
    input_error_count = 0

    if output_format not in SUPPORTED_REPORT_DATASET_FORMATS:
        raise ValueError(
            "output_format must be one of: " + ", ".join(SUPPORTED_REPORT_DATASET_FORMATS)
        )

    is_batch = (source / "index.json").exists()
    archive_validation_status = "not_checked"
    if require_archive_validation:
        validation = (
            validate_batch_report_archive(source) if is_batch else validate_report_bundle(source)
        )
        archive_validation_status = validation.status
        if validation.status != "pass":
            errors.extend(validation.errors)
            warnings.extend(validation.warnings)
            return _build_result(
                source_path=source,
                output_path=output,
                rows=rows,
                skipped_count=skipped_count,
                input_error_count=input_error_count,
                archive_validation_status=archive_validation_status,
                warnings=warnings,
                errors=errors,
            )

    if is_batch:
        batch_rows, skipped_count, input_error_count = _extract_batch_rows(source)
        rows.extend(batch_rows)
    else:
        try:
            rows.append(
                _extract_single_row(
                    source,
                    case_id=source.name,
                    source_archive_path=source,
                    archive_validation_status=archive_validation_status,
                )
            )
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"failed to extract single report bundle: {exc}")

    if output is not None and rows and not errors:
        _write_rows(rows, output, output_format)

    return _build_result(
        source_path=source,
        output_path=output,
        rows=rows,
        skipped_count=skipped_count,
        input_error_count=input_error_count,
        archive_validation_status=archive_validation_status,
        warnings=warnings,
        errors=errors,
    )


def extract_dataset_row_from_report_json(
    report_json_path: Path,
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Extract one flat dataset row from a generated `report.json` file."""
    report_path = Path(report_json_path)
    manifest = (
        report_path.with_name("manifest.json") if manifest_path is None else Path(manifest_path)
    )
    input_path = report_path.with_name("input.json")

    report = _read_json_object(report_path)
    input_data = _read_json_object(input_path) if input_path.exists() else {}
    report_input = _mapping(report.get("input_data"))
    geometry = _mapping(report.get("geometry"))
    reinforcement = _mapping(report.get("reinforcement"))
    longitudinal = _mapping(reinforcement.get("longitudinal"))
    transverse = _mapping(reinforcement.get("transverse"))
    checks = _mapping(report.get("checks"))
    bending = _mapping(checks.get("bending"))
    shear = _mapping(checks.get("shear"))
    crack_formation = _mapping(checks.get("crack_formation"))
    crack_width = _mapping(checks.get("crack_width"))
    deflection = _mapping(checks.get("deflection"))

    row: dict[str, Any] = {
        "dataset_source": REPORT_DATASET_SOURCE,
        "dataset_version": DATASET_VERSION,
        "case_id": report_path.parent.name,
        "source_archive_path": str(report_path.parent),
        "report_json_path": str(report_path),
        "input_json_path": str(input_path),
        "manifest_path": str(manifest),
        "input_sha256": compute_file_sha256(input_path) if input_path.exists() else None,
        "report_json_sha256": compute_file_sha256(report_path),
        "manifest_sha256": compute_file_sha256(manifest) if manifest.exists() else None,
        "archive_validation_status": "not_checked",
        "requires_engineer_review": report.get("requires_engineer_review"),
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "local_axes_id": _first_present(input_data, report_input, "local_axes_id"),
        "moment_axis": _first_present(input_data, report_input, "moment_axis"),
        "tension_face": _first_present(input_data, report_input, "tension_face"),
        "load_duration": _first_present(input_data, report_input, "load_duration"),
        "completeness_status": report.get("completeness_status"),
        "evidence_status": report.get("evidence_status"),
        "project_use_status": report.get("project_use_status"),
        "project_use": report.get("project_use"),
        "b": _first_present(input_data, report_input, "b"),
        "h": _first_present(input_data, report_input, "h"),
        "cover": _first_present(input_data, report_input, "cover"),
        "stirrup_diameter_for_geometry": _first_present(
            input_data,
            report_input,
            "stirrup_diameter_for_geometry",
        ),
        "concrete_class": _first_present(input_data, report_input, "concrete_class"),
        "longitudinal_rebar_class": _first_present(
            input_data,
            report_input,
            "longitudinal_rebar_class",
        ),
        "stirrup_rebar_class": _first_present(input_data, report_input, "stirrup_rebar_class"),
        "M": _first_present(input_data, report_input, "M"),
        "Q": _first_present(input_data, report_input, "Q"),
        "Mser": _first_present(input_data, report_input, "Mser"),
        "span": _first_present(input_data, report_input, "span"),
        "check_cracks": _first_present(input_data, report_input, "check_cracks"),
        "check_crack_width": _first_present(input_data, report_input, "check_crack_width"),
        "check_deflection": _first_present(input_data, report_input, "check_deflection"),
        "h0": geometry.get("h0"),
        "selected_main_bar_diameter": geometry.get("selected_main_bar_diameter"),
        "selected_longitudinal_scheme": geometry.get("selected_longitudinal_scheme"),
        "selected_transverse_scheme": geometry.get("selected_transverse_scheme"),
        "main_bar_count": longitudinal.get("bar_count"),
        "main_bar_diameter": longitudinal.get("diameter"),
        "longitudinal_as_mm2": longitudinal.get("As"),
        "stirrup_diameter": transverse.get("diameter"),
        "stirrup_legs": transverse.get("legs"),
        "stirrup_spacing": transverse.get("spacing"),
        "transverse_asw_mm2": transverse.get("Asw"),
        "bending_status": bending.get("status"),
        "bending_utilization": bending.get("utilization"),
        "Mult": bending.get("Mult"),
        "shear_status": shear.get("status"),
        "shear_utilization": shear.get("utilization"),
        "Qult": shear.get("Qult"),
        "crack_formation_status": crack_formation.get("status"),
        "Mcrc": crack_formation.get("Mcrc"),
        "crack_width_status": crack_width.get("status"),
        "acrc": crack_width.get("acrc"),
        "deflection_status": deflection.get("status"),
        "deflection": deflection.get("deflection"),
        "strength_status": report.get("strength_status"),
        "serviceability_status": report.get("serviceability_status"),
        "overall_status": report.get("overall_status"),
        "warnings_count": len(report.get("warnings", ()))
        if isinstance(report.get("warnings"), list)
        else 0,
        "external_validation_status": _optional_status(report, "external_validation_status"),
        "material_verification_status": _optional_status(report, "material_verification_status"),
    }
    _validate_report_dataset_safety_contract(row)
    return row


def _extract_batch_rows(source: Path) -> tuple[list[dict[str, Any]], int, int]:
    index = _read_json_object(source / "index.json")
    cases = index.get("cases")
    if not isinstance(cases, list):
        raise ValueError("batch index.json must contain a list field: cases")

    rows: list[dict[str, Any]] = []
    skipped_count = 0
    input_error_count = 0
    for case in cases:
        if not isinstance(case, dict):
            skipped_count += 1
            continue
        case_id = str(case.get("case_id") or f"case_{len(rows) + skipped_count + 1:03d}")
        if case.get("overall_status") == "input_error":
            input_error_count += 1
            skipped_count += 1
            continue
        case_dir = _case_dir_from_index_case(case, source)
        report_json_path = case_dir / "report.json"
        manifest_path = case_dir / "manifest.json"
        if not report_json_path.exists():
            skipped_count += 1
            continue
        row = extract_dataset_row_from_report_json(
            report_json_path,
            manifest_path=manifest_path,
        )
        row["case_id"] = case_id
        row["source_archive_path"] = str(source)
        row["archive_validation_status"] = "pass"
        rows.append(row)
    return rows, skipped_count, input_error_count


def _extract_single_row(
    source: Path,
    *,
    case_id: str,
    source_archive_path: Path,
    archive_validation_status: str,
) -> dict[str, Any]:
    row = extract_dataset_row_from_report_json(
        source / "report.json",
        manifest_path=source / "manifest.json",
    )
    row["case_id"] = case_id
    row["source_archive_path"] = str(source_archive_path)
    row["archive_validation_status"] = archive_validation_status
    return row


def _case_dir_from_index_case(case: Mapping[str, Any], source: Path) -> Path:
    manifest_path = case.get("manifest_path")
    if isinstance(manifest_path, str) and manifest_path:
        path = Path(manifest_path)
        if path.is_absolute() and path.exists():
            return path.parent
        for candidate in (Path.cwd() / path, source / path, source / path.name):
            if candidate.exists():
                return candidate.parent
    case_id = str(case.get("case_id") or "")
    return source / case_id


def _write_rows(rows: list[dict[str, Any]], output_path: Path, output_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "jsonl":
        output_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
            encoding="utf-8",
        )
        return
    if output_format == "json":
        output_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return
    _write_csv_rows(rows, output_path)


def _write_csv_rows(rows: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = _fieldnames(rows)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fieldnames(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    preferred = [
        "dataset_source",
        "dataset_version",
        "case_id",
        "source_archive_path",
        "report_json_path",
        "input_json_path",
        "manifest_path",
        "input_sha256",
        "report_json_sha256",
        "manifest_sha256",
        "archive_validation_status",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "load_duration",
        "completeness_status",
        "evidence_status",
        "project_use_status",
        "project_use",
        "requires_engineer_review",
        "ml_is_advisory_only",
        "deterministic_checks_required",
    ]
    keys = {key for row in rows for key in row}
    return [key for key in preferred if key in keys] + sorted(keys.difference(preferred))


def _read_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return data


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_present(primary: Mapping[str, Any], secondary: Mapping[str, Any], key: str) -> Any:
    if key in primary:
        return primary[key]
    return secondary.get(key)


def _optional_status(report: Mapping[str, Any], field_name: str) -> str:
    value = report.get(field_name)
    return str(value) if value else "not_provided"


def _validate_report_dataset_safety_contract(row: Mapping[str, Any]) -> None:
    if row.get("dataset_version") != DATASET_VERSION:
        raise ValueError(
            f"report dataset_version must be {DATASET_VERSION!r}"
        )
    RectangularBendingOrientation(
        local_axes_id=row.get("local_axes_id"),
        moment_axis=row.get("moment_axis"),
        tension_face=row.get("tension_face"),
    )
    if row.get("load_duration") != "short":
        raise ValueError("report dataset load_duration must be 'short'")
    if row.get("completeness_status") != "incomplete":
        raise ValueError(
            "report dataset completeness_status must be 'incomplete'"
        )
    if row.get("evidence_status") != "needs_engineer_review":
        raise ValueError(
            "report dataset evidence_status must be 'needs_engineer_review'"
        )
    if row.get("project_use_status") != "prohibited":
        raise ValueError(
            "report dataset project_use_status must be 'prohibited'"
        )
    if row.get("project_use") is not False:
        raise ValueError("report dataset project_use must be false")
    if row.get("requires_engineer_review") is not True:
        raise ValueError(
            "report dataset requires_engineer_review must be true"
        )


def _build_result(
    *,
    source_path: Path,
    output_path: Path | None,
    rows: list[dict[str, Any]],
    skipped_count: int,
    input_error_count: int,
    archive_validation_status: str,
    warnings: list[str],
    errors: list[str],
) -> ReportDatasetExportResult:
    if errors:
        status = "fail"
    elif skipped_count or input_error_count:
        status = "review_required"
    else:
        status = "pass"
    return ReportDatasetExportResult(
        status=status,
        source_path=str(source_path),
        output_path=None if output_path is None else str(output_path),
        row_count=len(rows),
        skipped_count=skipped_count,
        input_error_count=input_error_count,
        archive_validation_status=archive_validation_status,
        warnings=tuple(warnings),
        errors=tuple(errors),
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
    )
