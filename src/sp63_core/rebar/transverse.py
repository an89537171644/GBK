"""Transverse reinforcement selection by direct enumeration.

K3 is not a new normative formula. Each candidate is accepted only after
`check_shear_rectangular()` returns a passing result.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

from sp63_core.checks import ShearResult, check_shear_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import STIRRUP_DIAMETERS, Rebar, area_by_diameter
from sp63_core.rebar.constructive import (
    ConstructiveCheckResult,
    check_transverse_constructive,
)
from sp63_core.sections.rectangular import RectangularSection

DEFAULT_STIRRUP_LEGS: tuple[int, ...] = (2, 4)
DEFAULT_STIRRUP_SPACINGS: tuple[int, ...] = (100, 150, 200, 250, 300)
SHEAR_RULE_MAX_WARNING = (
    "stirrup spacing exceeds shear rule maximum for counting transverse reinforcement"
)
QSW_MIN_RULE_WARNING = "qsw is below draft minimum rule for counting transverse reinforcement"


@dataclass(frozen=True)
class TransverseRebarOption:
    """A passing transverse reinforcement candidate."""

    diameter: int
    legs: int
    spacing: int
    Asw: float
    scheme: str
    shear: ShearResult
    constructive: ConstructiveCheckResult
    section: RectangularSection
    steel_consumption: float
    status: str
    utilization: float
    warnings: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True


def select_transverse_rebar(
    section: RectangularSection,
    concrete: Concrete,
    stirrup_rebar: Rebar,
    Q: float,
    *,
    diameters: Iterable[int] = STIRRUP_DIAMETERS,
    legs_options: Iterable[int] = DEFAULT_STIRRUP_LEGS,
    spacings: Iterable[int] = DEFAULT_STIRRUP_SPACINGS,
    max_results: int = 5,
) -> tuple[TransverseRebarOption, ...]:
    """Return top passing transverse reinforcement options."""
    section.validate_geometry()
    if not isfinite(Q) or Q < 0:
        raise ValueError("Q must be a finite non-negative value")
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    candidate_diameters = tuple(diameters)
    candidate_legs = tuple(legs_options)
    candidate_spacings = tuple(spacings)
    if any(diameter <= 0 for diameter in candidate_diameters):
        raise ValueError("diameter must be positive")
    if any(legs <= 0 for legs in candidate_legs):
        raise ValueError("legs must be positive")
    if any(spacing <= 0 for spacing in candidate_spacings):
        raise ValueError("spacing must be positive")

    options: list[TransverseRebarOption] = []
    for diameter in candidate_diameters:
        candidate_section = RectangularSection(
            b=section.b,
            h=section.h,
            cover=section.cover,
            stirrup_diameter=diameter,
            main_bar_diameter=section.main_bar_diameter,
        )
        candidate_section.validate_geometry()
        for legs in candidate_legs:

            Asw = legs * area_by_diameter(diameter)
            for spacing in candidate_spacings:
                shear = check_shear_rectangular(
                    section=candidate_section,
                    concrete=concrete,
                    stirrup_rebar=stirrup_rebar,
                    Q=Q,
                    Asw=Asw,
                    sw=spacing,
                )
                if shear.status != "pass":
                    continue
                if _has_uncountable_transverse_warning(shear.warnings):
                    continue

                constructive = check_transverse_constructive(
                    section=candidate_section,
                    concrete=concrete,
                    stirrup_rebar=stirrup_rebar,
                    Q=Q,
                    stirrup_diameter=diameter,
                    Asw=Asw,
                    spacing=spacing,
                    element_type="beam",
                )
                if constructive.status == "fail":
                    continue

                steel_consumption = Asw / spacing
                options.append(
                    TransverseRebarOption(
                        diameter=diameter,
                        legs=legs,
                        spacing=spacing,
                        Asw=Asw,
                        scheme=f"D{diameter}/{spacing}, {legs} legs",
                        shear=shear,
                        constructive=constructive,
                        section=candidate_section,
                        steel_consumption=steel_consumption,
                        status=shear.status,
                        utilization=shear.utilization,
                        warnings=shear.warnings + constructive.warnings,
                    )
                )

    options.sort(
        key=lambda option: (option.steel_consumption, option.utilization, option.spacing)
    )
    return tuple(options[:max_results])


def _has_uncountable_transverse_warning(warnings: tuple[str, ...]) -> bool:
    return SHEAR_RULE_MAX_WARNING in warnings or QSW_MIN_RULE_WARNING in warnings
