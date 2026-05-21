"""Longitudinal reinforcement selection by direct enumeration.

D2 is not a new normative formula. Each candidate is accepted only after
`check_bending_rectangular()` returns a passing result.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sp63_core.checks import BendingResult, check_bending_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import LONGITUDINAL_DIAMETERS, Rebar, area_by_diameter
from sp63_core.sections.rectangular import RectangularSection

DEFAULT_BAR_COUNTS: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8)


@dataclass(frozen=True)
class LongitudinalRebarOption:
    """A passing longitudinal reinforcement candidate."""

    bar_count: int
    diameter: int
    As: float
    scheme: str
    bending: BendingResult
    requires_engineer_review: bool = True


def select_longitudinal_rebar(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    M: float,
    *,
    bar_counts: Iterable[int] = DEFAULT_BAR_COUNTS,
    diameters: Iterable[int] = LONGITUDINAL_DIAMETERS,
    max_results: int = 5,
    As_prime: float = 0.0,
    Rsc_override: float | None = None,
) -> tuple[LongitudinalRebarOption, ...]:
    """Return top passing longitudinal reinforcement options.

    Candidates are real schemes defined by bar count and bar diameter. Every
    candidate is checked through `check_bending_rectangular`; non-passing and
    review-required candidates are not returned.
    """
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    options: list[LongitudinalRebarOption] = []
    for bar_count in bar_counts:
        if bar_count <= 0:
            raise ValueError("bar_count must be positive")

        for diameter in diameters:
            As = bar_count * area_by_diameter(diameter)
            bending = check_bending_rectangular(
                section=section,
                concrete=concrete,
                rebar=rebar,
                As=As,
                As_prime=As_prime,
                M=M,
                Rsc_override=Rsc_override,
            )
            if bending.status != "pass":
                continue

            options.append(
                LongitudinalRebarOption(
                    bar_count=bar_count,
                    diameter=diameter,
                    As=As,
                    scheme=f"{bar_count}D{diameter}",
                    bending=bending,
                )
            )

    options.sort(key=lambda option: (option.As, option.bar_count, option.diameter))
    return tuple(options[:max_results])
