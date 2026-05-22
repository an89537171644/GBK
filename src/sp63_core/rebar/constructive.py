"""Draft constructive checks for reinforcement."""

from dataclasses import dataclass, field

from sp63_core.checks import check_shear_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import Rebar, get_rebar
from sp63_core.sections.rectangular import RectangularSection

LONGITUDINAL_SOURCE_CLAUSE = "SP 63.13330.2018 10.3.6, 10.3.9 draft MVP"
TRANSVERSE_SOURCE_CLAUSE = "SP 63.13330.2018 10.3.12-10.3.13 draft MVP"
MIN_LONGITUDINAL_RATIO_PERCENT = 0.1
MIN_STIRRUP_DIAMETER = 6.0


@dataclass(frozen=True)
class ConstructiveCheckResult:
    """Result of draft constructive reinforcement checks."""

    status: str
    warnings: tuple[str, ...]
    intermediate_values: dict[str, float | str | bool] = field(default_factory=dict)
    source_clause: str = TRANSVERSE_SOURCE_CLAUSE
    requires_engineer_review: bool = True


def check_longitudinal_constructive(
    section: RectangularSection,
    bar_count: int,
    As: float,
    *,
    element_type: str = "beam",
) -> ConstructiveCheckResult:
    """Check draft constructive longitudinal reinforcement requirements."""
    section.validate_geometry()
    if bar_count <= 0:
        raise ValueError("bar_count must be positive")
    if As <= 0:
        raise ValueError("As must be positive")

    b = section.b
    h0 = section.effective_depth()
    reinforcement_ratio_percent = As / (b * h0) * 100.0

    warnings: list[str] = []
    if element_type in ("beam", "slab", "rib"):
        min_reinforcement_ratio_percent = MIN_LONGITUDINAL_RATIO_PERCENT
    else:
        min_reinforcement_ratio_percent = MIN_LONGITUDINAL_RATIO_PERCENT

    if reinforcement_ratio_percent < min_reinforcement_ratio_percent:
        warnings.append("longitudinal reinforcement ratio is below minimum constructive value")
    if element_type in ("beam", "rib") and b > 150 and bar_count < 2:
        warnings.append("beam width greater than 150 mm requires at least two tensile bars")

    status = "fail" if warnings else "pass"
    intermediate_values: dict[str, float | str | bool] = {
        "b": b,
        "h0": h0,
        "As": As,
        "bar_count": bar_count,
        "reinforcement_ratio_percent": reinforcement_ratio_percent,
        "min_reinforcement_ratio_percent": min_reinforcement_ratio_percent,
        "source_clause": LONGITUDINAL_SOURCE_CLAUSE,
    }

    return ConstructiveCheckResult(
        status=status,
        warnings=tuple(warnings),
        intermediate_values=intermediate_values,
        source_clause=LONGITUDINAL_SOURCE_CLAUSE,
    )


def check_transverse_constructive(
    section: RectangularSection,
    concrete: Concrete,
    stirrup_rebar: Rebar,
    Q: float,
    stirrup_diameter: float,
    Asw: float,
    spacing: float,
    *,
    element_type: str = "beam",
) -> ConstructiveCheckResult:
    """Check draft constructive transverse reinforcement requirements."""
    section.validate_geometry()
    h0 = section.effective_depth()
    _validate_transverse_inputs(
        Q=Q,
        stirrup_diameter=stirrup_diameter,
        Asw=Asw,
        spacing=spacing,
    )

    warnings: list[str] = []
    if stirrup_diameter < MIN_STIRRUP_DIAMETER:
        warnings.append("stirrup diameter is less than 6 mm for bending elements")

    shear_without_stirrups = check_shear_rectangular(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=Q,
        Asw=0.0,
        sw=spacing,
    )
    transverse_required_by_calculation = shear_without_stirrups.status != "pass"
    sw_max_by_shear_rule = _sw_max_by_shear_rule(
        Rbt=concrete.Rbt,
        b=section.b,
        h0=h0,
        Q=Q,
    )
    if transverse_required_by_calculation:
        max_spacing = min(0.5 * h0, 300.0)
    else:
        max_spacing = min(0.75 * h0, 500.0)
        if element_type == "slab":
            warnings.append(
                "slab transverse reinforcement constructive rules are draft and require "
                "engineer review"
            )

    if spacing > max_spacing:
        warnings.append("stirrup spacing exceeds constructive maximum")
    if transverse_required_by_calculation and spacing > sw_max_by_shear_rule:
        warnings.append(
            "stirrup spacing exceeds shear rule maximum for counting transverse reinforcement"
        )

    status = _transverse_status(
        warnings=warnings,
        stirrup_diameter=stirrup_diameter,
        spacing=spacing,
        max_spacing=max_spacing,
        sw_max_by_shear_rule=sw_max_by_shear_rule,
        transverse_required_by_calculation=transverse_required_by_calculation,
    )
    intermediate_values: dict[str, float | str | bool] = {
        "h0": h0,
        "Q": Q,
        "stirrup_diameter": stirrup_diameter,
        "Asw": Asw,
        "spacing": spacing,
        "min_stirrup_diameter": MIN_STIRRUP_DIAMETER,
        "max_spacing": max_spacing,
        "sw_max_by_shear_rule": sw_max_by_shear_rule,
        "transverse_required_by_calculation": transverse_required_by_calculation,
        "shear_without_stirrups_status": shear_without_stirrups.status,
        "source_clause": TRANSVERSE_SOURCE_CLAUSE,
    }

    return ConstructiveCheckResult(
        status=status,
        warnings=tuple(warnings),
        intermediate_values=intermediate_values,
        source_clause=TRANSVERSE_SOURCE_CLAUSE,
    )


def check_transverse_spacing_constructive(
    section: RectangularSection,
    Q: float,
    concrete: Concrete,
    stirrup_diameter: float,
    spacing: float,
    *,
    element_type: str = "beam",
) -> ConstructiveCheckResult:
    """Backward-compatible wrapper for the first K6 transverse API."""
    return check_transverse_constructive(
        section=section,
        concrete=concrete,
        stirrup_rebar=get_rebar("A240"),
        Q=Q,
        stirrup_diameter=stirrup_diameter,
        Asw=0.0,
        spacing=spacing,
        element_type=element_type,
    )


def _validate_transverse_inputs(
    *, Q: float, stirrup_diameter: float, Asw: float, spacing: float
) -> None:
    if Q < 0:
        raise ValueError("Q must be non-negative")
    if stirrup_diameter <= 0:
        raise ValueError("stirrup_diameter must be positive")
    if Asw < 0:
        raise ValueError("Asw must be non-negative")
    if spacing <= 0:
        raise ValueError("spacing must be positive")


def _transverse_status(
    *,
    warnings: list[str],
    stirrup_diameter: float,
    spacing: float,
    max_spacing: float,
    sw_max_by_shear_rule: float,
    transverse_required_by_calculation: bool,
) -> str:
    if (
        stirrup_diameter < MIN_STIRRUP_DIAMETER
        or spacing > max_spacing
        or (transverse_required_by_calculation and spacing > sw_max_by_shear_rule)
    ):
        return "fail"
    if warnings:
        return "warning"
    return "pass"


def _sw_max_by_shear_rule(*, Rbt: float, b: float, h0: float, Q: float) -> float:
    """Return draft spacing limit for counting transverse reinforcement."""
    if Q <= 0:
        return float("inf")
    return Rbt * b * h0**2 / Q
