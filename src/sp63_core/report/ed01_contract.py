"""Fail-closed ED-01 publication contracts for public report data."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ALLOWED_CHECK_NAMES = frozenset(
    ("bending", "shear", "crack_formation", "crack_width", "deflection")
)


def public_report_contract_errors(report: Mapping[str, Any]) -> tuple[str, ...]:
    """Return ED-01 errors for a public deterministic report mapping."""
    errors: list[str] = []
    _validate_public_status_container(report, label="report", errors=errors)
    _validate_public_checks(report.get("checks"), label="report.checks", errors=errors)

    nested_report = report.get("report")
    if isinstance(nested_report, Mapping):
        _validate_public_status_container(
            nested_report,
            label="report.report",
            errors=errors,
        )
        _validate_public_checks(
            nested_report.get("checks"),
            label="report.report.checks",
            errors=errors,
        )
        protocol = nested_report.get("protocol")
    else:
        protocol = report.get("protocol")
    if not isinstance(protocol, Mapping):
        if _contains_bending_check(report) or _contains_bending_check(nested_report):
            errors.append("report.protocol must be an object when bending is present")
    else:
        _validate_public_status_container(protocol, label="report.protocol", errors=errors)
        _validate_public_checks(
            protocol.get("checks"),
            label="report.protocol.checks",
            errors=errors,
        )

    diagnostic_paths = tuple(_diagnostic_field_paths(report))
    if diagnostic_paths:
        errors.append(
            "public report must not contain diagnostic fields: "
            + ", ".join(diagnostic_paths)
        )
    return tuple(errors)


def public_report_dataset_row_errors(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Return ED-01 errors for one flattened public report-dataset row."""
    errors: list[str] = []
    if row.get("status_scope") != "public":
        errors.append("status_scope must be 'public'")
    bending_status = row.get("bending_status")
    if not _is_null_value(bending_status) and bending_status != "outside_applicability":
        errors.append("bending_status must be null or 'outside_applicability'")
    if not _is_null_value(row.get("bending_utilization")):
        errors.append("bending_utilization must be null")
    if not _is_null_value(row.get("Mult")):
        errors.append("Mult must be null")
    if row.get("strength_status") == "pass":
        errors.append("strength_status must not be 'pass' while ED-01 is open")
    if row.get("overall_status") == "pass":
        errors.append("overall_status must not be 'pass' while ED-01 is open")

    diagnostic_fields = sorted(
        str(key) for key in row if isinstance(key, str) and key.startswith("diagnostic_")
    )
    if diagnostic_fields:
        errors.append(
            "public report-dataset row must not contain diagnostic fields: "
            + ", ".join(diagnostic_fields)
        )
    return tuple(errors)


def _validate_public_status_container(
    value: Mapping[str, Any],
    *,
    label: str,
    errors: list[str],
) -> None:
    if value.get("status_scope") != "public":
        errors.append(f"{label}.status_scope must be 'public'")
    if value.get("strength_status") == "pass":
        errors.append(f"{label}.strength_status must not be 'pass' while ED-01 is open")
    if value.get("overall_status") == "pass":
        errors.append(f"{label}.overall_status must not be 'pass' while ED-01 is open")
    if value.get("status") == "pass":
        errors.append(f"{label}.status must not be 'pass' while ED-01 is open")


def _validate_public_checks(
    value: object,
    *,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"{label} must be an object")
        return

    unknown_names = tuple(name for name in value if name not in ALLOWED_CHECK_NAMES)
    if unknown_names:
        errors.append(
            f"{label} contains unknown check names: "
            + ", ".join(repr(name) for name in unknown_names)
        )

    if "bending" not in value:
        return
    bending = value.get("bending")
    if not isinstance(bending, Mapping):
        errors.append(f"{label}.bending must be an object")
        return
    if bending.get("status") != "outside_applicability":
        errors.append(f"{label}.bending.status must be 'outside_applicability'")
    if bending.get("public_status") != "outside_applicability":
        errors.append(f"{label}.bending.public_status must be 'outside_applicability'")
    if bending.get("status_scope") != "public":
        errors.append(f"{label}.bending.status_scope must be 'public'")
    if bending.get("Mult") is not None:
        errors.append(f"{label}.bending.Mult must be null")
    if bending.get("utilization") is not None:
        errors.append(f"{label}.bending.utilization must be null")
    if bending.get("capacity_applicable") is not False:
        errors.append(f"{label}.bending.capacity_applicable must be false")
    if bending.get("capacity_publication_allowed") is not False:
        errors.append(f"{label}.bending.capacity_publication_allowed must be false")


def _diagnostic_field_paths(value: object, *, path: str = "report") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and key.startswith("diagnostic_"):
                paths.append(child_path)
            paths.extend(_diagnostic_field_paths(nested, path=child_path))
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            paths.extend(_diagnostic_field_paths(nested, path=f"{path}[{index}]"))
    return tuple(paths)


def _is_null_value(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _contains_bending_check(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    checks = value.get("checks")
    return isinstance(checks, Mapping) and "bending" in checks
