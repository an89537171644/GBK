"""Draft constructive checks for transverse reinforcement."""

from dataclasses import dataclass, field

from sp63_core.checks import check_shear_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import get_rebar
from sp63_core.sections.rectangular import RectangularSection

SOURCE_CLAUSE = "SP 63.13330.2018 10.3.12-10.3.13 draft MVP"
MIN_STIRRUP_DIAMETER = 6.0


@dataclass(frozen=True)
class ConstructiveCheckResult:
    """Result of draft constructive transverse reinforcement checks."""

    status: str
    warnings: tuple[str, ...]
    intermediate_values: dict[str, float | str | bool] = field(default_factory=dict)
    source_clause: str = SOURCE_CLAUSE
    requires_engineer_review: bool = True


def check_transverse_spacing_constructive(
    section: RectangularSection,
    Q: float,
    concrete: Concrete,
    stirrup_diameter: float,
    spacing: float,
    *,
    element_type: str = "beam",
) -> ConstructiveCheckResult:
    """Check draft constructive stirrup diameter and spacing limits."""
    section.validate_geometry()
    h0 = section.effective_depth()
    _validate_inputs(stirrup_diameter=stirrup_diameter, spacing=spacing, Q=Q)

    warnings: list[str] = []
    if stirrup_diameter < MIN_STIRRUP_DIAMETER:
        warnings.append("stirrup diameter is less than 6 mm for bending elements")

    transverse_required_by_calculation = _transverse_required_by_calculation(
        section=section,
        concrete=concrete,
        Q=Q,
        spacing=spacing,
    )
    if transverse_required_by_calculation:
        max_spacing = min(0.5 * h0, 300.0)
    else:
        max_spacing = min(0.75 * h0, 500.0)
        if element_type == "slab":
            warnings.append(
                "slab transverse reinforcement rules are draft and require engineer review"
            )

    if spacing > max_spacing:
        warnings.append("stirrup spacing exceeds constructive maximum")

    status = _status_from_warnings(
        warnings=warnings,
        stirrup_diameter=stirrup_diameter,
        spacing=spacing,
        max_spacing=max_spacing,
    )
    intermediate_values: dict[str, float | str | bool] = {
        "h0": h0,
        "Q": Q,
        "stirrup_diameter": stirrup_diameter,
        "spacing": spacing,
        "min_stirrup_diameter": MIN_STIRRUP_DIAMETER,
        "max_spacing": max_spacing,
        "transverse_required_by_calculation": transverse_required_by_calculation,
        "source_clause": SOURCE_CLAUSE,
    }

    return ConstructiveCheckResult(
        status=status,
        warnings=tuple(warnings),
        intermediate_values=intermediate_values,
    )


def _validate_inputs(*, stirrup_diameter: float, spacing: float, Q: float) -> None:
    if stirrup_diameter <= 0:
        raise ValueError("stirrup_diameter must be positive")
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    if Q < 0:
        raise ValueError("Q must be non-negative")


def _transverse_required_by_calculation(
    *,
    section: RectangularSection,
    concrete: Concrete,
    Q: float,
    spacing: float,
) -> bool:
    shear_without_stirrups = check_shear_rectangular(
        section=section,
        concrete=concrete,
        stirrup_rebar=get_rebar("A240"),
        Q=Q,
        Asw=0.0,
        sw=spacing,
    )
    return shear_without_stirrups.status != "pass"


def _status_from_warnings(
    *,
    warnings: list[str],
    stirrup_diameter: float,
    spacing: float,
    max_spacing: float,
) -> str:
    if stirrup_diameter < MIN_STIRRUP_DIAMETER or spacing > max_spacing:
        return "fail"
    if warnings:
        return "warning"
    return "pass"
