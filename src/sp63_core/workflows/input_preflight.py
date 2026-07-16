"""Preflight validation report for engineering input JSON files.

This module is intentionally limited to input-shape and engineering-sanity checks.
It does not import or run deterministic calculation modules.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sp63_core.materials.concrete import CONCRETE_CATALOG
from sp63_core.materials.rebar import REBAR_CATALOG
from sp63_core.materials.uls_context import SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES
from sp63_core.workflows.input_form_schema import (
    MANDATORY_WARNINGS,
    InputFormSchemaResult,
    build_input_form_schema,
)

PREFLIGHT_WARNING = (
    "Input preflight is a validation/reporting step only. It does not perform "
    "design calculations and does not approve ML for project use."
)

DESIGN_REQUIRED_FIELDS = (
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
)

NONNEGATIVE_NUMERIC_FIELDS = ("M", "Q", "Mser")
POSITIVE_NUMERIC_FIELDS = (
    "b",
    "h",
    "cover",
    "stirrup_diameter_for_geometry",
    "span",
    "acrc_limit",
    "deflection_limit",
    "deflection_limit_ratio",
)
BOOLEAN_FIELDS = (
    "check_cracks",
    "check_crack_width",
    "check_deflection",
    "create_zip",
    "with_index",
    "include_ml_readiness",
)
PATH_FIELDS_TO_VERIFY = ("dataset_path", "external_validation_csv", "material_verification_csv")


@dataclass(frozen=True)
class InputPreflightIssue:
    """Single preflight issue found in an input JSON file."""

    issue_id: str
    severity: str
    field: str | None
    message: str
    engineering_hint: str


@dataclass(frozen=True)
class InputPreflightResult:
    """Machine-readable preflight validation result."""

    status: str
    preflight_status: str
    input_json_path: str
    output_dir: str | None
    checked_fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    missing_required_fields: tuple[str, ...]
    unknown_fields: tuple[str, ...]
    issue_count: int
    error_count: int
    warning_count: int
    issues: tuple[InputPreflightIssue, ...]
    json_data: dict[str, Any]
    markdown: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    requires_engineer_review: bool = True
    ml_is_advisory_only: bool = True
    deterministic_checks_required: bool = True
    ml_ready_for_project_use: bool = False


def run_input_preflight(
    input_json_path: Path,
    *,
    output_dir: Path | None = None,
    schema_result: InputFormSchemaResult | None = None,
) -> InputPreflightResult:
    """Validate an input JSON file before running engineering workflow commands."""
    schema = schema_result or build_input_form_schema()
    schema_fields = _schema_fields(schema)
    required_fields = tuple(field for field in DESIGN_REQUIRED_FIELDS if field in schema_fields)
    optional_fields = tuple(field for field in schema.optional_fields if field in schema_fields)
    issues: list[InputPreflightIssue] = []

    input_path = Path(input_json_path)
    data = _load_input_json(input_path, issues)
    if not isinstance(data, dict):
        data = {}

    unknown_fields = tuple(sorted(field for field in data if field not in schema_fields))
    for field in unknown_fields:
        _add_issue(
            issues,
            "unknown_field",
            "error",
            field,
            f"Unknown input field: {field}",
            "Use fields from input-form-schema only; do not pass ad-hoc workflow flags.",
        )

    missing_required = tuple(field for field in required_fields if field not in data)
    for field in missing_required:
        _add_issue(
            issues,
            "missing_required_field",
            "error",
            field,
            f"Missing required input field: {field}",
            "Fill all required geometry, material, and load fields before running workflow.",
        )

    if "ml_ready_for_project_use" in data:
        _add_issue(
            issues,
            "ml_ready_not_user_settable",
            "error",
            "ml_ready_for_project_use",
            "ml_ready_for_project_use must not be provided by users.",
            "This flag is a hard safety output and must remain false.",
        )

    _validate_numeric_fields(data, schema_fields, issues)
    _validate_boolean_fields(data, schema_fields, issues)
    _validate_declared_options(data, schema_fields, issues)
    _validate_geometry(data, issues)
    _validate_materials(data, issues)
    _validate_ml_and_paths(data, input_path, issues)

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = _status_from_counts(error_count=error_count, warning_count=warning_count)
    warnings = tuple(issue.message for issue in issues if issue.severity == "warning")
    errors = tuple(issue.message for issue in issues if issue.severity == "error")
    json_data = _build_preflight_json(
        status=status,
        input_json_path=input_path,
        output_dir=output_dir,
        checked_fields=tuple(data.keys()),
        required_fields=required_fields,
        optional_fields=optional_fields,
        missing_required_fields=missing_required,
        unknown_fields=unknown_fields,
        issues=tuple(issues),
        warnings=warnings,
        errors=errors,
    )
    markdown = render_input_preflight_markdown(json_data)
    result = InputPreflightResult(
        status=status,
        preflight_status=status,
        input_json_path=str(input_path),
        output_dir=str(output_dir) if output_dir is not None else None,
        checked_fields=tuple(data.keys()),
        required_fields=required_fields,
        optional_fields=optional_fields,
        missing_required_fields=missing_required,
        unknown_fields=unknown_fields,
        issue_count=len(issues),
        error_count=error_count,
        warning_count=warning_count,
        issues=tuple(issues),
        json_data=json_data,
        markdown=markdown,
        warnings=warnings,
        errors=errors,
        requires_engineer_review=True,
        ml_is_advisory_only=True,
        deterministic_checks_required=True,
        ml_ready_for_project_use=False,
    )
    if output_dir is not None:
        _write_preflight_files(Path(output_dir), result)
    return result


def render_input_preflight_markdown(json_data: dict[str, Any]) -> str:
    """Render preflight JSON data as Markdown."""
    lines = [
        "# Input JSON Preflight Report",
        "",
        PREFLIGHT_WARNING,
        "",
        "requires_engineer_review = true",
        "ml_is_advisory_only = true",
        "deterministic_checks_required = true",
        "ml_ready_for_project_use = false",
        "",
        "## Summary",
        "",
        f"- status: `{json_data['status']}`",
        f"- preflight_status: `{json_data['preflight_status']}`",
        f"- input_json_path: `{json_data['input_json_path']}`",
        f"- output_dir: `{json_data['output_dir']}`",
        f"- checked_fields: {len(json_data['checked_fields'])}",
        f"- issue_count: {json_data['issue_count']}",
        f"- error_count: {json_data['error_count']}",
        f"- warning_count: {json_data['warning_count']}",
        "",
        "## Missing Required Fields",
        "",
        *_bullet_lines(tuple(json_data["missing_required_fields"])),
        "",
        "## Unknown Fields",
        "",
        *_bullet_lines(tuple(json_data["unknown_fields"])),
        "",
        "## Issues",
        "",
        *_issue_table_lines(tuple(json_data["issues"])),
        "",
        "## Validation Scope",
        "",
        "- JSON must be an object.",
        "- Required geometry, material, and load fields must be present.",
        "- Numeric fields must have valid numeric values.",
        "- Geometry and serviceability assumptions are screened before workflow execution.",
        "- Material class names are checked against the current catalog.",
        "- Optional ML-readiness/external/material CSV paths are checked when provided.",
        "",
        "## Safety",
        "",
        "- This report does not run design calculations.",
        "- This report does not certify project use.",
        "- Deterministic SP63 checks remain mandatory.",
        "- Engineer review remains mandatory.",
        "- ML output remains advisory-only.",
    ]
    return "\n".join(lines) + "\n"


def _load_input_json(path: Path, issues: list[InputPreflightIssue]) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as input_file:
            data = json.load(input_file)
    except FileNotFoundError:
        _add_issue(
            issues,
            "input_json_missing",
            "error",
            None,
            f"Input JSON file does not exist: {path}",
            "Provide an existing JSON file before running the engineering workflow.",
        )
        return None
    except json.JSONDecodeError as exc:
        _add_issue(
            issues,
            "input_json_invalid",
            "error",
            None,
            f"Input JSON is not valid JSON: {exc.msg}",
            "Fix JSON syntax before running the engineering workflow.",
        )
        return None

    if not isinstance(data, dict):
        _add_issue(
            issues,
            "input_json_not_object",
            "error",
            None,
            "Input JSON must contain an object at the top level.",
            "Use a JSON object with named engineering input fields.",
        )
        return None
    return data


def _validate_numeric_fields(
    data: dict[str, Any],
    schema_fields: dict[str, dict[str, Any]],
    issues: list[InputPreflightIssue],
) -> None:
    for field, metadata in schema_fields.items():
        if field not in data or metadata.get("type") != "number" or data[field] is None:
            continue
        if not _is_number(data[field]):
            _add_issue(
                issues,
                "numeric_field_invalid",
                "error",
                field,
                f"{field} must be a numeric value.",
                "Use integer or floating-point numbers with project-consistent units.",
            )
            continue
        value = float(data[field])
        if field in POSITIVE_NUMERIC_FIELDS and value <= 0:
            _add_issue(
                issues,
                "positive_numeric_field_invalid",
                "error",
                field,
                f"{field} must be positive.",
                "Use physically meaningful positive dimensions and limits.",
            )
        if field in NONNEGATIVE_NUMERIC_FIELDS and value < 0:
            _add_issue(
                issues,
                "nonnegative_numeric_field_invalid",
                "error",
                field,
                f"{field} must be nonnegative.",
                "Design and service loads must not be negative in this workflow.",
            )


def _validate_boolean_fields(
    data: dict[str, Any],
    schema_fields: dict[str, dict[str, Any]],
    issues: list[InputPreflightIssue],
) -> None:
    for field in BOOLEAN_FIELDS:
        if field not in data or field not in schema_fields:
            continue
        if not isinstance(data[field], bool):
            _add_issue(
                issues,
                "boolean_field_invalid",
                "error",
                field,
                f"{field} must be true or false.",
                "Use JSON booleans, not strings or numbers.",
            )


def _validate_declared_options(
    data: dict[str, Any],
    schema_fields: dict[str, dict[str, Any]],
    issues: list[InputPreflightIssue],
) -> None:
    for field, metadata in schema_fields.items():
        if field not in data:
            continue
        value = data[field]
        if metadata.get("type") == "text":
            if not isinstance(value, str) or not value.strip():
                _add_issue(
                    issues,
                    "text_field_invalid",
                    "error",
                    field,
                    f"{field} must be a non-empty string.",
                    "Declare the source identifier explicitly.",
                )
            continue
        if metadata.get("type") != "select":
            continue
        options = metadata.get("options", ())
        if value not in options:
            _add_issue(
                issues,
                "select_field_invalid",
                "error",
                field,
                f"{field} must be one of: {', '.join(str(option) for option in options)}.",
                "Select an explicitly supported value from the input schema.",
            )


def _validate_geometry(data: dict[str, Any], issues: list[InputPreflightIssue]) -> None:
    h = _number_or_none(data.get("h"))
    cover = _number_or_none(data.get("cover"))
    span = _number_or_none(data.get("span"))
    m = _number_or_none(data.get("M"))
    mser = _number_or_none(data.get("Mser"))

    if h is not None and cover is not None and cover >= h:
        _add_issue(
            issues,
            "cover_not_less_than_h",
            "error",
            "cover",
            "cover must be less than h.",
            "Revise section height or cover before running deterministic checks.",
        )
    if h is not None and span is not None and span <= h:
        _add_issue(
            issues,
            "span_not_greater_than_h",
            "warning",
            "span",
            "span should be greater than h when span is provided.",
            "Engineer review is required for unusual span-to-depth input.",
        )
    if m is not None and mser is not None and mser > m:
        _add_issue(
            issues,
            "service_moment_above_design_moment",
            "warning",
            "Mser",
            "Mser is greater than M.",
            "Review load combination assumptions before running the workflow.",
        )


def _validate_materials(data: dict[str, Any], issues: list[InputPreflightIssue]) -> None:
    concrete_class = data.get("concrete_class")
    if concrete_class is not None and concrete_class not in CONCRETE_CATALOG:
        _add_issue(
            issues,
            "unknown_concrete_class",
            "error",
            "concrete_class",
            f"Unsupported concrete class: {concrete_class}",
            "Select a concrete class available in the material catalog.",
        )

    longitudinal_class = data.get("longitudinal_rebar_class")
    if longitudinal_class is not None and longitudinal_class not in REBAR_CATALOG:
        _add_issue(
            issues,
            "unknown_rebar_class",
            "error",
            "longitudinal_rebar_class",
            f"Unsupported reinforcement class: {longitudinal_class}",
            "Select a reinforcement class available in the material catalog.",
        )
    elif (
        longitudinal_class is not None
        and longitudinal_class not in SUPPORTED_ULS_LONGITUDINAL_REBAR_CLASSES
    ):
        _add_issue(
            issues,
            "unsupported_uls_longitudinal_rebar_class",
            "error",
            "longitudinal_rebar_class",
            f"Longitudinal reinforcement class is outside ULS v1 scope: {longitudinal_class}",
            "Select A400 or A500 for the current rectangular ULS design workflow.",
        )

    stirrup_class = data.get("stirrup_rebar_class")
    if stirrup_class is not None and stirrup_class not in REBAR_CATALOG:
        _add_issue(
            issues,
            "unknown_rebar_class",
            "error",
            "stirrup_rebar_class",
            f"Unsupported reinforcement class: {stirrup_class}",
            "Select a reinforcement class available in the material catalog.",
        )


def _validate_ml_and_paths(
    data: dict[str, Any],
    input_json_path: Path,
    issues: list[InputPreflightIssue],
) -> None:
    if data.get("include_ml_readiness") is True and not data.get("dataset_path"):
        _add_issue(
            issues,
            "dataset_required_for_ml_readiness",
            "error",
            "dataset_path",
            "dataset_path is required when include_ml_readiness is true.",
            "Provide a deterministic report-derived dataset path or disable ML readiness.",
        )

    for field in PATH_FIELDS_TO_VERIFY:
        value = data.get(field)
        if value in (None, ""):
            continue
        if not isinstance(value, str):
            _add_issue(
                issues,
                "path_field_invalid",
                "error",
                field,
                f"{field} must be a path string when provided.",
                "Use project-local paths and avoid private documents.",
            )
            continue
        if not _path_exists(value, input_json_path):
            _add_issue(
                issues,
                "path_field_missing",
                "error",
                field,
                f"{field} does not exist: {value}",
                "Create or select the referenced file before running this optional gate.",
            )


def _path_exists(value: str, input_json_path: Path) -> bool:
    path = Path(value)
    if path.exists():
        return True
    return not path.is_absolute() and (input_json_path.parent / path).exists()


def _build_preflight_json(
    *,
    status: str,
    input_json_path: Path,
    output_dir: Path | None,
    checked_fields: tuple[str, ...],
    required_fields: tuple[str, ...],
    optional_fields: tuple[str, ...],
    missing_required_fields: tuple[str, ...],
    unknown_fields: tuple[str, ...],
    issues: tuple[InputPreflightIssue, ...],
    warnings: tuple[str, ...],
    errors: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "report_type": "input_preflight_report",
        "status": status,
        "preflight_status": status,
        "input_json_path": str(input_json_path),
        "output_dir": str(output_dir) if output_dir is not None else None,
        "checked_fields": list(checked_fields),
        "required_fields": list(required_fields),
        "optional_fields": list(optional_fields),
        "missing_required_fields": list(missing_required_fields),
        "unknown_fields": list(unknown_fields),
        "issue_count": len(issues),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "issues": [asdict(issue) for issue in issues],
        "warnings": list(warnings),
        "errors": list(errors),
        "mandatory_warnings": [PREFLIGHT_WARNING, *MANDATORY_WARNINGS[1:]],
        "requires_engineer_review": True,
        "ml_is_advisory_only": True,
        "deterministic_checks_required": True,
        "ml_ready_for_project_use": False,
    }


def _write_preflight_files(output_dir: Path, result: InputPreflightResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "input_preflight_report.json").write_text(
        json.dumps(result.json_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "input_preflight_report.md").write_text(result.markdown, encoding="utf-8")


def _schema_fields(schema: InputFormSchemaResult) -> dict[str, dict[str, Any]]:
    groups = schema.json_data.get("groups", [])
    return {
        field["name"]: field
        for group in groups
        for field in group.get("fields", [])
        if "name" in field
    }


def _status_from_counts(*, error_count: int, warning_count: int) -> str:
    if error_count:
        return "fail"
    if warning_count:
        return "review_required"
    return "pass"


def _add_issue(
    issues: list[InputPreflightIssue],
    issue_id: str,
    severity: str,
    field: str | None,
    message: str,
    engineering_hint: str,
) -> None:
    issues.append(
        InputPreflightIssue(
            issue_id=issue_id,
            severity=severity,
            field=field,
            message=message,
            engineering_hint=engineering_hint,
        )
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _number_or_none(value: Any) -> float | None:
    if _is_number(value):
        return float(value)
    return None


def _bullet_lines(values: tuple[Any, ...]) -> list[str]:
    if not values:
        return ["- none"]
    return [f"- `{value}`" for value in values]


def _issue_table_lines(issues: tuple[dict[str, Any], ...]) -> list[str]:
    if not issues:
        return ["No issues found."]
    lines = [
        "| Severity | Field | Issue | Engineering hint |",
        "| --- | --- | --- | --- |",
    ]
    for issue in issues:
        field = issue.get("field") or "-"
        lines.append(
            "| {severity} | `{field}` | {message} | {hint} |".format(
                severity=issue["severity"],
                field=field,
                message=issue["message"],
                hint=issue["engineering_hint"],
            )
        )
    return lines
