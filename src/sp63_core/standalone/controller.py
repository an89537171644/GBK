"""Controller for a research-only standalone rectangular-beam workflow.

No calculation formula is implemented here.  The controller validates and
adapts manual inputs, invokes the existing engineering workflow, and validates
the resulting public report contract before returning any paths to the caller.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import zipfile
from contextlib import suppress
from dataclasses import asdict, replace
from html import escape
from math import isfinite
from pathlib import Path
from typing import Any

from sp63_core import __version__ as PACKAGE_VERSION
from sp63_core.design import RectangularDesignInput
from sp63_core.materials.rebar import REBAR_CATALOG, STIRRUP_DIAMETERS
from sp63_core.materials.uls_context import (
    SUPPORTED_ULS_CONCRETE_CLASSES,
    SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES,
)
from sp63_core.report import validate_report_bundle
from sp63_core.report.ed01_contract import public_report_contract_errors
from sp63_core.standalone.model import (
    STANDALONE_LOAD_DURATION,
    StandaloneBeamInput,
    StandaloneRunResult,
)
from sp63_core.units import kN_to_N, kNm_to_Nmm
from sp63_core.workflows.engineering_workflow import run_engineering_workflow

STANDALONE_WARNING = (
    "Research-only rectangular-beam preview. It does not certify a design, "
    "publish bending capacity, or authorize project use."
)
DIAGNOSTIC_SELECTION_WARNING = (
    "Any selected longitudinal or transverse reinforcement scheme and any local "
    "'pass' are diagnostic proposals only, not an approved design decision."
)
SLAB_STRIP_UNAVAILABLE_WARNING = (
    "Slab-strip mode is unavailable pending a separate engineering specification."
)
LOCAL_AXES_PREFIX = "standalone-rectangular-beam-v1"
OWNERSHIP_MARKER_FILENAME = ".gbk_standalone_output.json"
LATEST_STATUS_FILENAME = "standalone_latest_status.json"
LATEST_STATUS_TEMP_FILENAME = ".standalone_latest_status.tmp"
STANDALONE_INPUT_FILENAME = "standalone_input.json"
CANONICAL_INPUT_FILENAME = "canonical_input.json"
REVIEW_BUNDLE_FILENAME = "standalone_review_bundle.zip"
REVIEW_BUNDLE_TEMP_FILENAME = ".standalone_review_bundle.tmp"
REVIEW_MANIFEST_FILENAME = "standalone_review_manifest.json"
REVIEW_MANIFEST_SHA256_FILENAME = "standalone_review_manifest.sha256"
REVIEW_METADATA_FILENAME = "standalone_review_metadata.json"
WORKFLOW_SUMMARY_FILENAME = "workflow_summary.json"
STANDALONE_INDEX_FILENAME = "standalone_index.html"
RESULT_README_FILENAME = "README_STANDALONE_RESULT.md"
BUNDLE_STATUS_FILENAME = "standalone_bundle_status.json"
BUNDLE_INDEX_SOURCE_FILENAME = ".standalone_bundle_index.html"
BUNDLE_README_SOURCE_FILENAME = ".standalone_bundle_readme.md"
BUNDLE_README_MEMBER = "README_REVIEW_BUNDLE.md"
OWNERSHIP_MARKER_TYPE = "gbk_standalone_rectangular_beam_output"
OWNERSHIP_SCHEMA_VERSION = 1
KNOWN_OWNED_ARTIFACTS = (
    CANONICAL_INPUT_FILENAME,
    STANDALONE_INPUT_FILENAME,
    "workflow",
    LATEST_STATUS_FILENAME,
    LATEST_STATUS_TEMP_FILENAME,
    REVIEW_BUNDLE_FILENAME,
    REVIEW_BUNDLE_TEMP_FILENAME,
    REVIEW_MANIFEST_FILENAME,
    REVIEW_MANIFEST_SHA256_FILENAME,
    REVIEW_METADATA_FILENAME,
    WORKFLOW_SUMMARY_FILENAME,
    STANDALONE_INDEX_FILENAME,
    RESULT_README_FILENAME,
    BUNDLE_STATUS_FILENAME,
    BUNDLE_INDEX_SOURCE_FILENAME,
    BUNDLE_README_SOURCE_FILENAME,
)


def adapt_standalone_beam_input(input_data: StandaloneBeamInput) -> RectangularDesignInput:
    """Validate a manual standalone input and adapt it to the existing core DTO."""
    _validate_standalone_input(input_data)
    moment_n_mm = kNm_to_Nmm(input_data.moment_kNm)
    shear_n = kN_to_N(input_data.shear_kN)
    if not isfinite(moment_n_mm):
        raise ValueError("moment_kNm unit conversion must remain finite")
    if not isfinite(shear_n):
        raise ValueError("shear_kN unit conversion must remain finite")
    return RectangularDesignInput(
        b=float(input_data.b_mm),
        h=float(input_data.h_mm),
        cover=float(input_data.cover_mm),
        stirrup_diameter_for_geometry=float(input_data.stirrup_diameter_mm),
        concrete_class=input_data.concrete_class.strip().upper(),
        longitudinal_rebar_class=input_data.longitudinal_rebar_class.strip().upper(),
        stirrup_rebar_class=input_data.stirrup_rebar_class.strip().upper(),
        M=moment_n_mm,
        Q=shear_n,
        local_axes_id=f"{LOCAL_AXES_PREFIX}:{input_data.case_id.strip()}",
        moment_axis="local_z",
        tension_face=input_data.tension_face,
        load_duration=STANDALONE_LOAD_DURATION,
        check_cracks=False,
        check_crack_width=False,
        check_deflection=False,
    )


def run_standalone_beam_case(
    input_data: StandaloneBeamInput,
    output_dir: Path,
) -> StandaloneRunResult:
    """Run one beam case through preflight, reporting, and public-contract gates."""
    try:
        output_path = Path(output_dir)
    except TypeError as exc:
        return _failed_result(
            case_id=_safe_case_id(input_data),
            errors=(f"output directory validation failed: {exc}",),
        )

    output_owned, ownership_errors = _prepare_owned_output(output_path)
    latest_status_path = output_path / LATEST_STATUS_FILENAME
    if ownership_errors:
        result = _failed_result(
            case_id=_safe_case_id(input_data),
            errors=ownership_errors,
            latest_status_path=latest_status_path if output_owned else None,
        )
        return _finalize_result(
            result,
            output_path=output_path,
            output_owned=output_owned,
        )

    try:
        design_input = adapt_standalone_beam_input(input_data)
    except (TypeError, ValueError) as exc:
        result = _failed_result(
            case_id=_safe_case_id(input_data),
            errors=(f"input validation failed: {exc}",),
            latest_status_path=latest_status_path,
        )
        return _finalize_result(result, output_path=output_path, output_owned=True)

    standalone_input_path = output_path / STANDALONE_INPUT_FILENAME
    canonical_input_path = output_path / CANONICAL_INPUT_FILENAME
    workflow_dir = output_path / "workflow"
    deterministic_dir = workflow_dir / "deterministic_report"
    report_path = deterministic_dir / "report.json"
    workflow_index_path = workflow_dir / "index.html"
    standalone_index_path = output_path / STANDALONE_INDEX_FILENAME
    deterministic_zip_path = workflow_dir / "deterministic_report.zip"
    review_bundle_path = output_path / REVIEW_BUNDLE_FILENAME

    try:
        _write_json(
            standalone_input_path,
            _normalized_standalone_input_mapping(input_data),
        )
        _write_json(
            canonical_input_path,
            _design_input_mapping(design_input),
        )
        workflow = run_engineering_workflow(
            input_json_path=canonical_input_path,
            output_dir=workflow_dir,
            include_ml_readiness=False,
            create_zip=True,
            with_index=True,
            with_preflight=True,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        result = _failed_result(
            case_id=input_data.case_id.strip(),
            errors=(f"standalone workflow failed: {exc}",),
            input_json_path=(
                canonical_input_path if canonical_input_path.exists() else None
            ),
            standalone_input_path=(
                standalone_input_path if standalone_input_path.exists() else None
            ),
            canonical_input_path=(
                canonical_input_path if canonical_input_path.exists() else None
            ),
            latest_status_path=latest_status_path,
        )
        return _finalize_result(result, output_path=output_path, output_owned=True)

    warnings = tuple(
        dict.fromkeys(
            (
                STANDALONE_WARNING,
                SLAB_STRIP_UNAVAILABLE_WARNING,
                DIAGNOSTIC_SELECTION_WARNING,
                *workflow.warnings,
            )
        )
    )
    errors = list(workflow.errors)

    if workflow.preflight_status == "fail":
        errors.append("standalone preflight failed; calculation was not performed")
    if workflow.project_use is not False:
        errors.append("standalone workflow violated project_use=false")
    if workflow.ml_readiness_status is not None:
        errors.append("standalone workflow must not include ML readiness")
    if not workflow_index_path.exists():
        errors.append(f"standalone workflow index is missing: {workflow_index_path}")

    report_payload: dict[str, Any] | None = None
    if not report_path.exists():
        errors.append(f"standalone public report is missing: {report_path}")
    else:
        try:
            loaded_report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"standalone public report cannot be read: {exc}")
        else:
            if not isinstance(loaded_report, dict):
                errors.append("standalone public report must contain a JSON object")
            else:
                report_payload = loaded_report
                errors.extend(
                    f"standalone public report contract: {error}"
                    for error in public_report_contract_errors(report_payload)
                )
                if report_payload.get("project_use") is not False:
                    errors.append("standalone public report must keep project_use=false")

    if deterministic_dir.exists():
        archive_validation = validate_report_bundle(deterministic_dir)
        errors.extend(
            f"standalone report archive: {error}" for error in archive_validation.errors
        )
        if archive_validation.status != "pass":
            errors.append(
                "standalone report archive validation must pass before exposing outputs"
            )

    status = "fail" if errors else _standalone_status(workflow.status)
    expose_outputs = not errors and status != "fail"
    result = StandaloneRunResult(
        case_id=input_data.case_id.strip(),
        status=status,
        preflight_status=workflow.preflight_status or "not_run",
        calculation_status=workflow.deterministic_report_status,
        evidence_status=workflow.evidence_status,
        project_use=False,
        input_json_path=str(canonical_input_path),
        standalone_input_path=str(standalone_input_path),
        canonical_input_path=str(canonical_input_path),
        latest_status_path=str(latest_status_path),
        report_dir=str(deterministic_dir) if expose_outputs else None,
        report_index_path=(
            str(standalone_index_path)
            if expose_outputs and workflow_index_path.exists()
            else None
        ),
        report_zip_path=str(review_bundle_path) if expose_outputs else None,
        deterministic_report_zip_path=(
            str(deterministic_zip_path)
            if expose_outputs and deterministic_zip_path.exists()
            else None
        ),
        warnings=warnings,
        errors=tuple(dict.fromkeys(errors)),
    )
    return _finalize_result(result, output_path=output_path, output_owned=True)


def _validate_standalone_input(input_data: StandaloneBeamInput) -> None:
    if not isinstance(input_data, StandaloneBeamInput):
        raise TypeError("input_data must be StandaloneBeamInput")
    if not isinstance(input_data.case_id, str) or not input_data.case_id.strip():
        raise ValueError("case_id must be a non-empty string")
    if len(input_data.case_id.strip()) > 100:
        raise ValueError("case_id must be at most 100 characters")
    if any(ord(character) < 32 for character in input_data.case_id):
        raise ValueError("case_id must not contain control characters")

    numeric_values = {
        "b_mm": input_data.b_mm,
        "h_mm": input_data.h_mm,
        "cover_mm": input_data.cover_mm,
        "stirrup_diameter_mm": input_data.stirrup_diameter_mm,
        "moment_kNm": input_data.moment_kNm,
        "shear_kN": input_data.shear_kN,
    }
    for name, value in numeric_values.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"{name} must be a number")
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")

    for name in ("b_mm", "h_mm", "cover_mm", "stirrup_diameter_mm"):
        if numeric_values[name] <= 0:
            raise ValueError(f"{name} must be positive")
    if input_data.stirrup_diameter_mm not in STIRRUP_DIAMETERS:
        supported = ", ".join(str(value) for value in STIRRUP_DIAMETERS)
        raise ValueError(f"stirrup_diameter_mm must be one of: {supported}")
    if input_data.cover_mm >= input_data.h_mm:
        raise ValueError("cover_mm must be less than h_mm")
    if input_data.moment_kNm < 0:
        raise ValueError("moment_kNm must be non-negative")
    if input_data.shear_kN < 0:
        raise ValueError("shear_kN must be non-negative")

    concrete_class = _normalized_class(input_data.concrete_class, "concrete_class")
    if concrete_class not in SUPPORTED_ULS_CONCRETE_CLASSES:
        supported = ", ".join(sorted(SUPPORTED_ULS_CONCRETE_CLASSES))
        raise ValueError(f"concrete_class must be one of: {supported}")
    longitudinal_class = _normalized_class(
        input_data.longitudinal_rebar_class,
        "longitudinal_rebar_class",
    )
    if longitudinal_class not in SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES:
        supported = ", ".join(sorted(SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES))
        raise ValueError(f"longitudinal_rebar_class must be one of: {supported}")
    stirrup_class = _normalized_class(input_data.stirrup_rebar_class, "stirrup_rebar_class")
    if stirrup_class not in REBAR_CATALOG:
        supported = ", ".join(sorted(REBAR_CATALOG))
        raise ValueError(f"stirrup_rebar_class must be one of: {supported}")
    if input_data.tension_face not in ("local_y_min", "local_y_max"):
        raise ValueError("tension_face must be 'local_y_min' or 'local_y_max'")


def _normalized_class(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field_name} must be a non-empty string")
    return value.strip().upper()


def _normalized_standalone_input_mapping(
    input_data: StandaloneBeamInput,
) -> dict[str, Any]:
    return {
        "element_type": "rectangular_beam",
        "load_duration": STANDALONE_LOAD_DURATION,
        "case_id": input_data.case_id.strip(),
        "b_mm": float(input_data.b_mm),
        "h_mm": float(input_data.h_mm),
        "cover_mm": float(input_data.cover_mm),
        "stirrup_diameter_mm": float(input_data.stirrup_diameter_mm),
        "concrete_class": input_data.concrete_class.strip().upper(),
        "longitudinal_rebar_class": input_data.longitudinal_rebar_class.strip().upper(),
        "stirrup_rebar_class": input_data.stirrup_rebar_class.strip().upper(),
        "moment_kNm": float(input_data.moment_kNm),
        "shear_kN": float(input_data.shear_kN),
        "tension_face": input_data.tension_face,
    }


def _design_input_mapping(design_input: RectangularDesignInput) -> dict[str, Any]:
    data = asdict(design_input)
    allowed_fields = (
        "b",
        "h",
        "cover",
        "stirrup_diameter_for_geometry",
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
        "M",
        "Q",
        "local_axes_id",
        "moment_axis",
        "tension_face",
        "load_duration",
        "check_cracks",
        "check_crack_width",
        "check_deflection",
    )
    return {field: data[field] for field in allowed_fields}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        f"{json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)}\n",
        encoding="utf-8",
    )


def _prepare_owned_output(output_path: Path) -> tuple[bool, tuple[str, ...]]:
    """Claim an empty output or clean only artifacts in an owned output."""
    try:
        if output_path.is_symlink():
            return False, (
                "output directory must not be a symbolic link; no files were changed",
            )
        if output_path.exists():
            if not output_path.is_dir():
                return False, (
                    "output path must be a directory; no files were changed",
                )
            entries = tuple(output_path.iterdir())
            if entries:
                marker_errors = _ownership_marker_errors(output_path)
                if marker_errors:
                    return False, marker_errors
                return True, _clear_owned_artifacts(output_path)
        else:
            output_path.mkdir(parents=True, exist_ok=False)

        _write_json(
            output_path / OWNERSHIP_MARKER_FILENAME,
            {
                "marker_type": OWNERSHIP_MARKER_TYPE,
                "schema_version": OWNERSHIP_SCHEMA_VERSION,
                "owned_artifacts": list(KNOWN_OWNED_ARTIFACTS),
            },
        )
        return True, ()
    except OSError as exc:
        return False, (f"output directory preparation failed: {exc}",)


def _ownership_marker_errors(output_path: Path) -> tuple[str, ...]:
    marker_path = output_path / OWNERSHIP_MARKER_FILENAME
    refusal = (
        "refusing to use non-empty output directory without a valid standalone "
        "ownership marker; no files were changed"
    )
    if marker_path.is_symlink() or not marker_path.is_file():
        return (refusal,)
    try:
        payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (refusal,)
    if not isinstance(payload, dict):
        return (refusal,)
    valid = (
        payload.get("marker_type") == OWNERSHIP_MARKER_TYPE
        and payload.get("schema_version") == OWNERSHIP_SCHEMA_VERSION
        and payload.get("owned_artifacts") == list(KNOWN_OWNED_ARTIFACTS)
    )
    return () if valid else (refusal,)


def _clear_owned_artifacts(output_path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    for relative_name in KNOWN_OWNED_ARTIFACTS:
        try:
            _remove_owned_artifact(output_path / relative_name)
        except OSError as exc:
            errors.append(f"cannot clear owned artifact {relative_name}: {exc}")
    return tuple(errors)


def _remove_owned_artifact(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _finalize_result(
    result: StandaloneRunResult,
    *,
    output_path: Path,
    output_owned: bool,
) -> StandaloneRunResult:
    if not output_owned:
        return _sanitize_failed_result(result, latest_status_path=None)
    if result.status == "fail":
        return _finalize_failed_result(result, output_path=output_path)

    latest_status_path = output_path / LATEST_STATUS_FILENAME
    result = replace(result, latest_status_path=str(latest_status_path))
    status_error = _persist_latest_status(result, output_path=output_path)
    if status_error is not None:
        failed = replace(
            result,
            status="fail",
            errors=tuple(dict.fromkeys((*result.errors, status_error))),
        )
        cleanup_errors = _remove_failure_report_artifacts(output_path)
        return _sanitize_failed_result(
            replace(
                failed,
                errors=tuple(dict.fromkeys((*failed.errors, *cleanup_errors))),
            ),
            latest_status_path=None,
        )

    bundle_errors = _build_review_bundle(result, output_path=output_path)
    if bundle_errors:
        failed = replace(
            result,
            status="fail",
            errors=tuple(dict.fromkeys((*result.errors, *bundle_errors))),
        )
        return _finalize_failed_result(failed, output_path=output_path)
    return result


def _finalize_failed_result(
    result: StandaloneRunResult,
    *,
    output_path: Path,
) -> StandaloneRunResult:
    cleanup_errors = _remove_failure_report_artifacts(output_path)
    failed = _sanitize_failed_result(
        replace(
            result,
            errors=tuple(dict.fromkeys((*result.errors, *cleanup_errors))),
        ),
        latest_status_path=str(output_path / LATEST_STATUS_FILENAME),
    )
    status_error = _persist_latest_status(failed, output_path=output_path)
    if status_error is None:
        return failed

    with suppress(OSError):
        _remove_owned_artifact(output_path / LATEST_STATUS_FILENAME)
        _remove_owned_artifact(output_path / LATEST_STATUS_TEMP_FILENAME)
    return _sanitize_failed_result(
        replace(
            failed,
            errors=tuple(dict.fromkeys((*failed.errors, status_error))),
        ),
        latest_status_path=None,
    )


def _sanitize_failed_result(
    result: StandaloneRunResult,
    *,
    latest_status_path: str | None,
) -> StandaloneRunResult:
    return replace(
        result,
        status="fail",
        project_use=False,
        latest_status_path=latest_status_path,
        report_dir=None,
        report_index_path=None,
        report_zip_path=None,
        deterministic_report_zip_path=None,
    )


def _remove_failure_report_artifacts(output_path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    for relative_name in (
        "workflow",
        REVIEW_BUNDLE_FILENAME,
        REVIEW_BUNDLE_TEMP_FILENAME,
        REVIEW_MANIFEST_FILENAME,
        REVIEW_MANIFEST_SHA256_FILENAME,
        REVIEW_METADATA_FILENAME,
        WORKFLOW_SUMMARY_FILENAME,
        STANDALONE_INDEX_FILENAME,
        RESULT_README_FILENAME,
        BUNDLE_STATUS_FILENAME,
        BUNDLE_INDEX_SOURCE_FILENAME,
        BUNDLE_README_SOURCE_FILENAME,
    ):
        try:
            _remove_owned_artifact(output_path / relative_name)
        except OSError as exc:
            errors.append(f"cannot remove failed report artifact {relative_name}: {exc}")
    return tuple(errors)


def _persist_latest_status(
    result: StandaloneRunResult,
    *,
    output_path: Path,
) -> str | None:
    latest_path = output_path / LATEST_STATUS_FILENAME
    temporary_path = output_path / LATEST_STATUS_TEMP_FILENAME
    payload = {
        "report_type": "standalone_latest_status",
        "schema_version": 1,
        **asdict(result),
    }
    try:
        _remove_owned_artifact(temporary_path)
        _write_json(temporary_path, payload)
        temporary_path.replace(latest_path)
    except (OSError, TypeError, ValueError) as exc:
        with suppress(OSError):
            _remove_owned_artifact(temporary_path)
        return f"cannot persist standalone latest status: {exc}"
    return None


def _build_review_bundle(
    result: StandaloneRunResult,
    *,
    output_path: Path,
) -> tuple[str, ...]:
    metadata_path = output_path / REVIEW_METADATA_FILENAME
    summary_path = output_path / WORKFLOW_SUMMARY_FILENAME
    bundle_status_path = output_path / BUNDLE_STATUS_FILENAME
    standalone_index_path = output_path / STANDALONE_INDEX_FILENAME
    result_readme_path = output_path / RESULT_README_FILENAME
    bundle_index_source_path = output_path / BUNDLE_INDEX_SOURCE_FILENAME
    bundle_readme_source_path = output_path / BUNDLE_README_SOURCE_FILENAME
    manifest_path = output_path / REVIEW_MANIFEST_FILENAME
    manifest_sha256_path = output_path / REVIEW_MANIFEST_SHA256_FILENAME
    bundle_path = output_path / REVIEW_BUNDLE_FILENAME
    temporary_bundle_path = output_path / REVIEW_BUNDLE_TEMP_FILENAME
    deterministic_report_dir = output_path / "workflow" / "deterministic_report"
    build_id, code_identity_status = _safe_build_identity()

    metadata = {
        "report_type": "standalone_review_metadata",
        "schema_version": 1,
        "path_scope": "bundle_relative",
        "code_identity": {
            "package_name": "sp63_core",
            "package_version": PACKAGE_VERSION,
            "build_id": build_id,
            "code_identity_status": code_identity_status,
            "requires_engineer_review": True,
        },
        "scope": {
            "element_type": "rectangular_beam",
            "load_duration": STANDALONE_LOAD_DURATION,
            "status_scope": "public",
            "project_use": False,
            "requires_engineer_review": True,
            "reinforcement_selection_status": "diagnostic_only",
            "ml_included": False,
        },
        "units_layer": {
            "classification": "programmatic_input_unit_conversion",
            "normative_formula_asserted": False,
            "conversions": [
                {
                    "source_field": "moment_kNm",
                    "source_unit": "kN*m",
                    "target_field": "M",
                    "target_unit": "N*mm",
                    "implementation": "sp63_core.units.kNm_to_Nmm",
                },
                {
                    "source_field": "shear_kN",
                    "source_unit": "kN",
                    "target_field": "Q",
                    "target_unit": "N",
                    "implementation": "sp63_core.units.kN_to_N",
                },
            ],
        },
        "input_semantics": {
            "cover_reference": "concrete_face_to_outer_stirrup_surface",
            "moment_value_semantics": "non_negative_magnitude",
            "shear_value_semantics": "non_negative_magnitude",
            "tension_face_allowed": ["local_y_min", "local_y_max"],
            "physical_axis_mapping_status": "requires_engineer_review/open_question",
        },
    }
    summary = {
        "report_type": "standalone_workflow_summary",
        "schema_version": 1,
        "path_scope": "bundle_relative",
        "case_id": result.case_id,
        "status": result.status,
        "preflight_status": result.preflight_status,
        "calculation_status": result.calculation_status,
        "evidence_status": result.evidence_status,
        "project_use": False,
        "requires_engineer_review": True,
        "reinforcement_selection_status": result.reinforcement_selection_status,
        "landing_page": "index.html",
        "deterministic_report": "deterministic_report/report.json",
        "warning_count": len(result.warnings),
        "error_count": len(result.errors),
    }
    bundle_status = {
        "report_type": "standalone_bundle_status",
        "schema_version": 1,
        "path_scope": "bundle_relative",
        "case_id": result.case_id,
        "status": result.status,
        "preflight_status": result.preflight_status,
        "calculation_status": result.calculation_status,
        "evidence_status": result.evidence_status,
        "project_use": False,
        "project_use_status": "prohibited",
        "requires_engineer_review": True,
        "reinforcement_selection_status": result.reinforcement_selection_status,
        "paths": {
            "standalone_input": STANDALONE_INPUT_FILENAME,
            "canonical_input": CANONICAL_INPUT_FILENAME,
            "landing_page": "index.html",
            "result_readme": BUNDLE_README_MEMBER,
            "review_metadata": REVIEW_METADATA_FILENAME,
            "workflow_summary": WORKFLOW_SUMMARY_FILENAME,
            "deterministic_report": "deterministic_report/report.json",
        },
    }
    payload_sources = (
        (STANDALONE_INPUT_FILENAME, output_path / STANDALONE_INPUT_FILENAME),
        (CANONICAL_INPUT_FILENAME, output_path / CANONICAL_INPUT_FILENAME),
        (BUNDLE_STATUS_FILENAME, bundle_status_path),
        (REVIEW_METADATA_FILENAME, metadata_path),
        (WORKFLOW_SUMMARY_FILENAME, summary_path),
        ("index.html", bundle_index_source_path),
        (BUNDLE_README_MEMBER, bundle_readme_source_path),
        (
            "deterministic_report/input.json",
            deterministic_report_dir / "input.json",
        ),
        (
            "deterministic_report/report.json",
            deterministic_report_dir / "report.json",
        ),
        (
            "deterministic_report/report.md",
            deterministic_report_dir / "report.md",
        ),
        (
            "deterministic_report/report.html",
            deterministic_report_dir / "report.html",
        ),
    )

    try:
        _write_json(metadata_path, metadata)
        _write_json(summary_path, summary)
        _write_json(bundle_status_path, bundle_status)
        standalone_index_path.write_text(
            _standalone_index_html(result),
            encoding="utf-8",
        )
        result_readme_path.write_text(
            _standalone_result_readme(result),
            encoding="utf-8",
        )
        bundle_index_source_path.write_text(
            _bundle_index_html(result),
            encoding="utf-8",
        )
        bundle_readme_source_path.write_text(
            _bundle_readme(result),
            encoding="utf-8",
        )
        for archive_name, source_path in payload_sources:
            if source_path.is_symlink() or not source_path.is_file():
                raise ValueError(f"review bundle source is missing or unsafe: {archive_name}")
        privacy_errors = _bundle_privacy_errors(payload_sources, output_path=output_path)
        if privacy_errors:
            raise ValueError("; ".join(privacy_errors))
        manifest = {
            "report_type": "standalone_review_bundle_manifest",
            "schema_version": 1,
            "path_scope": "bundle_relative",
            "bundle_filename": REVIEW_BUNDLE_FILENAME,
            "project_use": False,
            "requires_engineer_review": True,
            "reinforcement_selection_status": result.reinforcement_selection_status,
            "files": [
                {
                    "path": archive_name,
                    "sha256": _sha256_file(source_path),
                    "size_bytes": source_path.stat().st_size,
                }
                for archive_name, source_path in payload_sources
            ],
        }
        _write_json(manifest_path, manifest)
        manifest_sha256_path.write_bytes(
            (
                f"{_sha256_file(manifest_path)}  "
                f"{REVIEW_MANIFEST_FILENAME}\n"
            ).encode("ascii")
        )
        _remove_owned_artifact(temporary_bundle_path)
        with zipfile.ZipFile(
            temporary_bundle_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for archive_name, source_path in payload_sources:
                archive.write(source_path, archive_name)
            archive.write(manifest_path, REVIEW_MANIFEST_FILENAME)
            archive.write(manifest_sha256_path, REVIEW_MANIFEST_SHA256_FILENAME)
        temporary_bundle_path.replace(bundle_path)
        validation_errors = _review_bundle_errors(bundle_path)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        _remove_owned_artifact(bundle_index_source_path)
        _remove_owned_artifact(bundle_readme_source_path)
    except (OSError, TypeError, ValueError, zipfile.BadZipFile) as exc:
        with suppress(OSError):
            _remove_owned_artifact(temporary_bundle_path)
        return (f"standalone review bundle failed: {exc}",)
    return ()


def _review_bundle_errors(bundle_path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    expected_payload_names = {
        STANDALONE_INPUT_FILENAME,
        CANONICAL_INPUT_FILENAME,
        BUNDLE_STATUS_FILENAME,
        REVIEW_METADATA_FILENAME,
        WORKFLOW_SUMMARY_FILENAME,
        "index.html",
        BUNDLE_README_MEMBER,
        "deterministic_report/input.json",
        "deterministic_report/report.json",
        "deterministic_report/report.md",
        "deterministic_report/report.html",
    }
    expected_names = expected_payload_names | {
        REVIEW_MANIFEST_FILENAME,
        REVIEW_MANIFEST_SHA256_FILENAME,
    }
    try:
        with zipfile.ZipFile(bundle_path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                errors.append("review bundle contains duplicate archive members")
            if set(names) != expected_names:
                errors.append("review bundle members do not match the required contract")
            manifest_bytes = archive.read(REVIEW_MANIFEST_FILENAME)
            manifest = json.loads(manifest_bytes.decode("utf-8"))
            if not isinstance(manifest, dict):
                errors.append("review bundle manifest must be a JSON object")
                return tuple(errors)
            if manifest.get("path_scope") != "bundle_relative":
                errors.append("review bundle manifest path_scope must be bundle_relative")
            records = manifest.get("files")
            if not isinstance(records, list):
                errors.append("review bundle manifest files must be a list")
                return tuple(errors)
            recorded_names: set[str] = set()
            for record in records:
                if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                    errors.append("review bundle manifest contains an invalid file record")
                    continue
                name = record["path"]
                recorded_names.add(name)
                try:
                    data = archive.read(name)
                except KeyError:
                    errors.append(f"review bundle manifest member is missing: {name}")
                    continue
                if hashlib.sha256(data).hexdigest() != record.get("sha256"):
                    errors.append(f"review bundle checksum mismatch: {name}")
                if len(data) != record.get("size_bytes"):
                    errors.append(f"review bundle size mismatch: {name}")
            if recorded_names != expected_payload_names:
                errors.append("review bundle manifest records do not match required payloads")
            expected_sidecar = (
                f"{hashlib.sha256(manifest_bytes).hexdigest()}  "
                f"{REVIEW_MANIFEST_FILENAME}\n"
            )
            actual_sidecar = archive.read(REVIEW_MANIFEST_SHA256_FILENAME).decode("utf-8")
            if actual_sidecar != expected_sidecar:
                errors.append("review bundle manifest sidecar checksum mismatch")
    except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        errors.append(f"review bundle cannot be validated: {exc}")
    return tuple(errors)


def _bundle_privacy_errors(
    payload_sources: tuple[tuple[str, Path], ...],
    *,
    output_path: Path,
) -> tuple[str, ...]:
    sensitive_fragments: set[bytes] = {
        b"/tmp/",
        b"/private/tmp/",
        b"/workspace/",
    }
    for path in (output_path, Path.cwd(), Path.home()):
        with suppress(OSError):
            resolved = str(path.resolve()).encode("utf-8")
            if len(resolved) > 3:
                sensitive_fragments.add(resolved)

    errors: list[str] = []
    for archive_name, source_path in payload_sources:
        data = source_path.read_bytes()
        contains_posix_path = any(fragment in data for fragment in sensitive_fragments)
        contains_windows_user_path = bool(
            re.search(rb"[A-Za-z]:[\\/]Users[\\/]", data, flags=re.IGNORECASE)
        )
        if contains_posix_path or contains_windows_user_path:
            errors.append(
                "review bundle privacy guard found a producer-local path in "
                f"{archive_name}"
            )
    return tuple(errors)


def _safe_build_identity() -> tuple[str | None, str]:
    value = os.environ.get("GBK_BUILD_ID")
    if value is None or value == "source-unverified":
        return None, "unavailable_open_question"
    match = re.fullmatch(r"wheel-sha256:([0-9a-fA-F]{64})", value)
    if match is not None:
        normalized = f"wheel-sha256:{match.group(1).lower()}"
        return normalized, "recorded_from_launcher_requires_manifest_match"
    return None, "invalid_ignored"


def _standalone_index_html(result: StandaloneRunResult) -> str:
    values = {
        "case_id": escape(result.case_id, quote=True),
        "status": escape(result.status, quote=True),
        "preflight": escape(result.preflight_status, quote=True),
        "calculation": escape(result.calculation_status, quote=True),
        "evidence": escape(result.evidence_status, quote=True),
        "reinforcement": escape(result.reinforcement_selection_status, quote=True),
    }
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GBK — исследовательский результат</title>
  <style>
    body {{ max-width: 880px; margin: 2rem auto; padding: 0 1rem;
      font-family: sans-serif; line-height: 1.5; }}
    .warning {{ border: 3px solid #a40000; background: #fff1f0; padding: 1rem; }}
    dt {{ font-weight: 700; }} dd {{ margin-bottom: .5rem; }}
    code {{ background: #eee; padding: .1rem .25rem; }}
  </style>
</head>
<body>
  <h1>Результат автономного исследовательского маршрута GBK</h1>
  <div class="warning">
    <strong>Не для проектного применения.</strong>
    <code>project_use=false</code>; <code>requires_engineer_review=true</code>.
    Подбор продольной и поперечной арматуры имеет статус <code>{values['reinforcement']}</code>.
    Любой локальный статус <code>pass</code> не является общим допуском конструкции.
  </div>
  <h2>Статусы</h2>
  <dl>
    <dt>Случай</dt><dd>{values['case_id']}</dd>
    <dt>Общий статус</dt><dd>{values['status']}</dd>
    <dt>Предварительная проверка</dt><dd>{values['preflight']}</dd>
    <dt>Расчётный маршрут</dt><dd>{values['calculation']}</dd>
    <dt>Инженерные подтверждения</dt><dd>{values['evidence']}</dd>
  </dl>
  <h2>Материалы</h2>
  <ul>
    <li><a href="{REVIEW_BUNDLE_FILENAME}">Пакет для передачи рецензенту</a> —
      передавать следует только этот архив.</li>
    <li><a href="workflow/index.html">Локальный необработанный отчёт workflow</a> —
      вторичный диагностический материал.</li>
    <li><a href="workflow/deterministic_report.zip">Локальный диагностический архив</a> —
      не предназначен для передачи и может содержать пути
      компьютера-производителя.</li>
    <li><a href="{RESULT_README_FILENAME}">Пояснение к результату</a>.</li>
  </ul>
</body>
</html>
"""


def _bundle_index_html(result: StandaloneRunResult) -> str:
    values = {
        "case_id": escape(result.case_id, quote=True),
        "status": escape(result.status, quote=True),
        "preflight": escape(result.preflight_status, quote=True),
        "calculation": escape(result.calculation_status, quote=True),
        "evidence": escape(result.evidence_status, quote=True),
        "reinforcement": escape(result.reinforcement_selection_status, quote=True),
    }
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GBK — пакет инженерной рецензии</title>
</head>
<body>
  <h1>Пакет инженерной рецензии GBK</h1>
  <p><strong>Не для проектного применения.</strong>
    <code>project_use=false</code>; <code>requires_engineer_review=true</code>.
    Подбор арматуры: <code>{values['reinforcement']}</code>.
    Любой локальный <code>pass</code> не является общим допуском.</p>
  <dl>
    <dt>Случай</dt><dd>{values['case_id']}</dd>
    <dt>Общий статус</dt><dd>{values['status']}</dd>
    <dt>Предварительная проверка</dt><dd>{values['preflight']}</dd>
    <dt>Расчётный маршрут</dt><dd>{values['calculation']}</dd>
    <dt>Инженерные подтверждения</dt><dd>{values['evidence']}</dd>
  </dl>
  <ul>
    <li><a href="deterministic_report/report.html">Отчёт HTML</a></li>
    <li><a href="deterministic_report/report.json">Отчёт JSON</a></li>
    <li><a href="deterministic_report/report.md">Отчёт Markdown</a></li>
    <li><a href="standalone_input.json">Исходные данные в единицах пользователя</a></li>
    <li><a href="canonical_input.json">Канонические данные расчётного ядра</a></li>
    <li><a href="standalone_bundle_status.json">Статус пакета</a></li>
    <li><a href="standalone_review_metadata.json">Метаданные области и единиц</a></li>
    <li><a href="workflow_summary.json">Сводка маршрута</a></li>
    <li><a href="standalone_review_manifest.json">Манифест контрольных сумм</a></li>
    <li><a href="{BUNDLE_README_MEMBER}">Пояснение к пакету</a></li>
  </ul>
</body>
</html>
"""


def _standalone_result_readme(result: StandaloneRunResult) -> str:
    case_id = _markdown_inline(result.case_id)
    status = _markdown_inline(result.status)
    preflight = _markdown_inline(result.preflight_status)
    calculation = _markdown_inline(result.calculation_status)
    evidence = _markdown_inline(result.evidence_status)
    reinforcement = _markdown_inline(result.reinforcement_selection_status)
    return f"""# Автономный исследовательский результат GBK

Случай: `{case_id}`.

- общий статус: `{status}`;
- предварительная проверка: `{preflight}`;
- расчётный маршрут: `{calculation}`;
- инженерные подтверждения: `{evidence}`;
- `project_use=false`;
- `requires_engineer_review=true`;
- подбор арматуры: `{reinforcement}`.

Любой локальный статус `pass` не является общим допуском конструкции или
разрешением проектного применения.

Для передачи рецензенту используйте только `{REVIEW_BUNDLE_FILENAME}`.
Файлы `workflow/index.html` и `workflow/deterministic_report.zip` являются
локальными диагностическими материалами; внутренний ZIP не предназначен для
передачи и может содержать локальные пути компьютера-производителя.
"""


def _bundle_readme(result: StandaloneRunResult) -> str:
    case_id = _markdown_inline(result.case_id)
    status = _markdown_inline(result.status)
    reinforcement = _markdown_inline(result.reinforcement_selection_status)
    return f"""# Пакет инженерной рецензии GBK

Случай: `{case_id}`; статус: `{status}`.

Пакет имеет `path_scope=bundle_relative`, `project_use=false`,
`requires_engineer_review=true`. Подбор арматуры имеет статус
`{reinforcement}`. Любой локальный `pass` не является общим допуском.

Начните с `index.html`. Детерминированные материалы находятся в каталоге
`deterministic_report/`; исходные данные — в `standalone_input.json` и
`canonical_input.json`; контрольные суммы — в
`standalone_review_manifest.json`.
"""


def _markdown_inline(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("`", "\\`")
    return escaped.replace("<", "&lt;").replace(">", "&gt;")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _standalone_status(workflow_status: str) -> str:
    if workflow_status == "fail":
        return "fail"
    if workflow_status == "outside_applicability":
        return "outside_applicability"
    return "review_required"


def _safe_case_id(input_data: object) -> str:
    if isinstance(input_data, StandaloneBeamInput) and isinstance(input_data.case_id, str):
        return input_data.case_id.strip()
    return "invalid-case"


def _failed_result(
    *,
    case_id: str,
    errors: tuple[str, ...],
    input_json_path: Path | None = None,
    standalone_input_path: Path | None = None,
    canonical_input_path: Path | None = None,
    latest_status_path: Path | None = None,
) -> StandaloneRunResult:
    return StandaloneRunResult(
        case_id=case_id,
        status="fail",
        preflight_status="not_run",
        calculation_status="not_run",
        evidence_status="needs_engineer_review",
        project_use=False,
        input_json_path=str(input_json_path) if input_json_path is not None else None,
        standalone_input_path=(
            str(standalone_input_path) if standalone_input_path is not None else None
        ),
        canonical_input_path=(
            str(canonical_input_path) if canonical_input_path is not None else None
        ),
        latest_status_path=(
            str(latest_status_path) if latest_status_path is not None else None
        ),
        report_dir=None,
        report_index_path=None,
        report_zip_path=None,
        deterministic_report_zip_path=None,
        warnings=(
            STANDALONE_WARNING,
            SLAB_STRIP_UNAVAILABLE_WARNING,
            DIAGNOSTIC_SELECTION_WARNING,
        ),
        errors=errors,
    )
