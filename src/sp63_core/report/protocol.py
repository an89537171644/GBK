"""Calculation protocol assembly for the SP 63 MVP."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Literal

ProtocolStatus = Literal["pass", "fail", "review_or_fail", "outside_applicability"]
GroupStatus = Literal[
    "pass", "fail", "review_or_fail", "outside_applicability", "not_checked"
]

STRENGTH_CHECKS = frozenset(("bending", "shear"))
SERVICEABILITY_CHECKS = frozenset(("crack_formation", "crack_width", "deflection"))
SERVICEABILITY_PASS_LIKE_STATUSES = frozenset(("pass", "no_crack", "not_required"))


@dataclass(frozen=True)
class CalculationProtocol:
    """Structured calculation protocol for one checked reinforcement scheme."""

    input_data: dict[str, Any]
    materials: dict[str, Any]
    geometry: dict[str, Any]
    reinforcement: dict[str, Any]
    checks: dict[str, dict[str, Any]]
    warnings: tuple[str, ...]
    strength_status: GroupStatus
    serviceability_status: GroupStatus
    overall_status: ProtocolStatus
    status: ProtocolStatus
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-like dictionary representation."""
        return {
            "input_data": self.input_data,
            "materials": self.materials,
            "geometry": self.geometry,
            "reinforcement": self.reinforcement,
            "checks": self.checks,
            "warnings": list(self.warnings),
            "strength_status": self.strength_status,
            "serviceability_status": self.serviceability_status,
            "overall_status": self.overall_status,
            "status": self.status,
            "completeness_status": self.completeness_status,
            "evidence_status": self.evidence_status,
            "project_use_status": self.project_use_status,
            "project_use": self.project_use,
            "requires_engineer_review": self.requires_engineer_review,
        }


def build_calculation_protocol(
    *,
    input_data: Mapping[str, Any],
    materials: Mapping[str, Any],
    geometry: Mapping[str, Any],
    reinforcement: Mapping[str, Any],
    checks: Mapping[str, Any],
) -> CalculationProtocol:
    """Build a structured protocol from input data and calculation results."""
    if not checks:
        raise ValueError("checks must not be empty")

    normalized_checks = {name: _check_to_dict(check) for name, check in checks.items()}
    warnings = _collect_warnings(normalized_checks)
    strength_status = _strength_status(normalized_checks)
    serviceability_status = _serviceability_status(normalized_checks)
    overall_status = _overall_status(
        strength_status=strength_status,
        serviceability_status=serviceability_status,
    )

    return CalculationProtocol(
        input_data=dict(input_data),
        materials=dict(materials),
        geometry=dict(geometry),
        reinforcement=dict(reinforcement),
        checks=normalized_checks,
        warnings=warnings,
        strength_status=strength_status,
        serviceability_status=serviceability_status,
        overall_status=overall_status,
        status=overall_status,
        requires_engineer_review=True,
    )


def _check_to_dict(check: Any) -> dict[str, Any]:
    if is_dataclass(check) and not isinstance(check, type):
        return asdict(check)
    if isinstance(check, Mapping):
        return dict(check)
    raise TypeError("check results must be dataclasses or mappings")


def _collect_warnings(checks: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    warnings: list[str] = []
    for check_name, check in checks.items():
        for warning in check.get("warnings", ()):
            warnings.append(f"{check_name}: {warning}")
    return tuple(warnings)


def _strength_status(checks: Mapping[str, Mapping[str, Any]]) -> GroupStatus:
    strength_checks = [check for name, check in checks.items() if name in STRENGTH_CHECKS]
    if not strength_checks:
        return "not_checked"
    if any(check.get("status") == "outside_applicability" for check in strength_checks):
        return "outside_applicability"
    if all(check.get("status") == "pass" for check in strength_checks):
        return "pass"
    return "fail"


def _serviceability_status(checks: Mapping[str, Mapping[str, Any]]) -> GroupStatus:
    serviceability_checks = {
        name: check for name, check in checks.items() if name in SERVICEABILITY_CHECKS
    }
    if not serviceability_checks:
        return "not_checked"
    if any(check.get("status") == "fail" for check in serviceability_checks.values()):
        return "fail"

    crack_formation = serviceability_checks.get("crack_formation")
    crack_width_present = "crack_width" in serviceability_checks
    if (
        crack_formation is not None
        and crack_formation.get("status") == "crack"
        and not crack_width_present
    ):
        return "review_or_fail"

    for name, check in serviceability_checks.items():
        status = check.get("status")
        if name == "crack_formation" and status == "crack" and crack_width_present:
            continue
        if status not in SERVICEABILITY_PASS_LIKE_STATUSES:
            return "review_or_fail"
    return "pass"


def _overall_status(
    *,
    strength_status: GroupStatus,
    serviceability_status: GroupStatus,
) -> ProtocolStatus:
    if (
        strength_status == "outside_applicability"
        or serviceability_status == "outside_applicability"
    ):
        return "outside_applicability"
    if strength_status == "fail" or serviceability_status == "fail":
        return "fail"
    if serviceability_status == "review_or_fail":
        return "review_or_fail"
    if strength_status == "pass" and serviceability_status in ("pass", "not_checked"):
        return "pass"
    return "review_or_fail"
