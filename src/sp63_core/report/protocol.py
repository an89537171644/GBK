"""Calculation protocol assembly for the SP 63 MVP."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Literal

ProtocolStatus = Literal["pass", "fail", "review_or_fail"]


@dataclass(frozen=True)
class CalculationProtocol:
    """Structured calculation protocol for one checked reinforcement scheme."""

    input_data: dict[str, Any]
    materials: dict[str, Any]
    geometry: dict[str, Any]
    reinforcement: dict[str, Any]
    checks: dict[str, dict[str, Any]]
    warnings: tuple[str, ...]
    status: ProtocolStatus
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
            "status": self.status,
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
    status = _overall_status(normalized_checks)

    return CalculationProtocol(
        input_data=dict(input_data),
        materials=dict(materials),
        geometry=dict(geometry),
        reinforcement=dict(reinforcement),
        checks=normalized_checks,
        warnings=warnings,
        status=status,
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


def _overall_status(checks: Mapping[str, Mapping[str, Any]]) -> ProtocolStatus:
    statuses = [check.get("status") for check in checks.values()]
    if "review_or_fail" in statuses:
        return "review_or_fail"
    pass_like_statuses = {"pass", "no_crack", "crack"}
    if all(status in pass_like_statuses for status in statuses):
        return "pass"
    return "fail"
