"""Transverse reinforcement selection by direct enumeration."""

from collections.abc import Iterable
from dataclasses import dataclass

from sp63_core.checks import ShearResult, check_shear_rectangular
from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import STIRRUP_DIAMETERS, Rebar, area_by_diameter
from sp63_core.sections.rectangular import RectangularSection

DEFAULT_LEGS_OPTIONS: tuple[int, ...] = (2, 4)
DEFAULT_SPACING_OPTIONS: tuple[float, ...] = (100, 150, 200, 250, 300)


@dataclass(frozen=True)
class TransverseRebarOption:
    """A passing transverse reinforcement candidate."""

    diameter: int
    legs: int
    spacing: float
    Asw: float
    steel_per_meter: float
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
    legs_options: Iterable[int] = DEFAULT_LEGS_OPTIONS,
    spacing_options: Iterable[float] = DEFAULT_SPACING_OPTIONS,
    max_results: int = 5,
    c_points: int = 101,
) -> tuple[TransverseRebarOption, ...]:
    """Return top passing transverse reinforcement options."""
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    options: list[TransverseRebarOption] = []
    for diameter in diameters:
        if diameter <= 0:
            raise ValueError("diameter must be positive")

        for legs in legs_options:
            if legs <= 0:
                raise ValueError("legs must be positive")

            for spacing in spacing_options:
                if spacing <= 0:
                    raise ValueError("spacing must be positive")

                Asw = legs * area_by_diameter(diameter)
                shear = check_shear_rectangular(
                    section=section,
                    concrete=concrete,
                    stirrup_rebar=stirrup_rebar,
                    Q=Q,
                    Asw=Asw,
                    sw=spacing,
                    c_points=c_points,
                )
                if shear.status != "pass":
                    continue

                steel_per_meter = Asw / spacing * 1000.0
                options.append(
                    TransverseRebarOption(
                        diameter=diameter,
                        legs=legs,
                        spacing=spacing,
                        Asw=Asw,
                        steel_per_meter=steel_per_meter,
                        scheme=f"{legs}D{diameter}/{spacing:g}",
                        shear=shear,
                        status=shear.status,
                        utilization=shear.utilization,
                        warnings=shear.warnings,
                    )
                )

    options.sort(
        key=lambda option: (
            option.steel_per_meter,
            -option.spacing,
            option.diameter,
            option.legs,
        )
    )
    return tuple(options[:max_results])
