"""Longitudinal reinforcement selection by direct enumeration.

D2 is not a new normative formula. Each candidate is accepted only after
`check_bending_rectangular()` returns a passing result.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

from sp63_core.checks import BendingResult, check_bending_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import (
    LONGITUDINAL_DIAMETERS,
    LoadDuration,
    Rebar,
    area_by_diameter,
)
from sp63_core.materials.uls_context import (
    UnsupportedULSMaterialProfileError,
    resolve_uls_material_context,
)
from sp63_core.rebar.constructive import (
    ConstructiveCheckResult,
    check_longitudinal_constructive,
)
from sp63_core.rebar.layout import RebarLayout, check_single_layer_layout
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

DEFAULT_BAR_COUNTS: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8)


@dataclass(frozen=True)
class LongitudinalRebarOption:
    """A diagnostic longitudinal reinforcement candidate pending ED-01."""

    bar_count: int
    diameter: int
    As: float
    scheme: str
    bending: BendingResult
    section: RectangularSection
    layout: RebarLayout
    constructive: ConstructiveCheckResult
    status: str
    utilization: float | None
    diagnostic_status: str
    diagnostic_utilization: float
    warnings: tuple[str, ...]
    requires_engineer_review: bool = True


def select_longitudinal_rebar(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    M: float,
    *,
    orientation: RectangularBendingOrientation,
    load_duration: LoadDuration,
    bar_counts: Iterable[int] = DEFAULT_BAR_COUNTS,
    diameters: Iterable[int] = LONGITUDINAL_DIAMETERS,
    max_results: int = 5,
    min_clear_spacing: float = 25.0,
) -> tuple[LongitudinalRebarOption, ...]:
    """Return top passing longitudinal reinforcement options.

    Candidates are real schemes defined by bar count and bar diameter. Every
    candidate is checked through `check_bending_rectangular`; only narrow
    deterministic passes with feasible layout are returned. Every returned
    option still requires engineer review and remains prohibited for project
    use.
    """
    if not isinstance(orientation, RectangularBendingOrientation):
        raise TypeError("orientation must be RectangularBendingOrientation")
    section.validate_geometry()
    if not isfinite(M) or M < 0:
        raise ValueError("M must be a finite non-negative value")
    if not isfinite(min_clear_spacing) or min_clear_spacing <= 0:
        raise ValueError("min_clear_spacing must be a finite positive value")
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    counts = tuple(bar_counts)
    candidate_diameters = tuple(diameters)
    if any(bar_count <= 0 for bar_count in counts):
        raise ValueError("bar_count must be positive")
    if any(diameter <= 0 for diameter in candidate_diameters):
        raise ValueError("diameter must be positive")

    try:
        resolve_uls_material_context(concrete, rebar, load_duration)
    except UnsupportedULSMaterialProfileError:
        return ()

    options: list[LongitudinalRebarOption] = []
    for bar_count in counts:
        for diameter in candidate_diameters:
            candidate_section = RectangularSection(
                b=section.b,
                h=section.h,
                cover=section.cover,
                stirrup_diameter=section.stirrup_diameter,
                main_bar_diameter=diameter,
            )
            layout = check_single_layer_layout(
                section=candidate_section,
                bar_count=bar_count,
                diameter=diameter,
                min_clear_spacing=min_clear_spacing,
            )
            if not layout.layout_feasible:
                continue

            As = bar_count * area_by_diameter(diameter)
            constructive = check_longitudinal_constructive(
                section=candidate_section,
                bar_count=bar_count,
                As=As,
                element_type="beam",
            )
            if constructive.status == "fail":
                continue

            bending = check_bending_rectangular(
                section=candidate_section,
                concrete=concrete,
                rebar=rebar,
                As=As,
                M=M,
                orientation=orientation,
                load_duration=load_duration,
            )
            if bending.diagnostic_status != "pass":
                continue
            if (
                bending.diagnostic_Mult is None
                or bending.diagnostic_utilization is None
            ):
                raise RuntimeError(
                    "passing diagnostic bending result must include diagnostic values"
                )

            options.append(
                LongitudinalRebarOption(
                    bar_count=bar_count,
                    diameter=diameter,
                    As=As,
                    scheme=f"{bar_count}D{diameter}",
                    bending=bending,
                    section=candidate_section,
                    layout=layout,
                    constructive=constructive,
                    status=bending.public_status,
                    utilization=None,
                    diagnostic_status=bending.diagnostic_status,
                    diagnostic_utilization=bending.diagnostic_utilization,
                    warnings=layout.warnings + constructive.warnings + bending.warnings,
                )
            )

    options.sort(key=lambda option: (option.As, option.bar_count, option.diameter))
    return tuple(options[:max_results])
