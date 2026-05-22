"""Transverse reinforcement selection by direct enumeration.

K3 is not a new normative formula. Each candidate is accepted only after
`check_shear_rectangular()` returns a passing result.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sp63_core.checks import ShearResult, check_shear_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import STIRRUP_DIAMETERS, Rebar, area_by_diameter
from sp63_core.sections.rectangular import RectangularSection

DEFAULT_STIRRUP_LEGS: tuple[int, ...] = (2, 4)
DEFAULT_STIRRUP_SPACINGS: tuple[int, ...] = (100, 150, 200, 250, 300)


@dataclass(frozen=True)
class TransverseRebarOption:
    """A passing transverse reinforcement candidate."""

    diameter: int
    legs: int
    spacing: int
    Asw: float
    scheme: str
    shear: ShearResult
    status: str
    utilization: float
    warnings: tuple[str, ...]
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
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    options: list[TransverseRebarOption] = []
    for diameter in diameters:
        for legs in legs_options:
            if legs <= 0:
                raise ValueError("legs must be positive")

            Asw = legs * area_by_diameter(diameter)
            for spacing in spacings:
                shear = check_shear_rectangular(
                    section=section,
                    concrete=concrete,
                    stirrup_rebar=stirrup_rebar,
                    Q=Q,
                    Asw=Asw,
                    sw=spacing,
                )
                if shear.status != "pass":
                    continue

                options.append(
                    TransverseRebarOption(
                        diameter=diameter,
                        legs=legs,
                        spacing=spacing,
                        Asw=Asw,
                        scheme=f"D{diameter}/{spacing}, {legs} legs",
                        shear=shear,
                        status=shear.status,
                        utilization=shear.utilization,
                        warnings=shear.warnings,
                    )
                )

    options.sort(key=lambda option: (option.Asw / option.spacing, option.Asw, option.spacing))
    return tuple(options[:max_results])
