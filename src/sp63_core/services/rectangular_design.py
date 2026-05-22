"""End-to-end rectangular element design service for the SP 63 MVP."""

from dataclasses import dataclass
from typing import Literal

from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import Rebar
from sp63_core.rebar import (
    LongitudinalRebarOption,
    TransverseRebarOption,
    select_longitudinal_rebar,
    select_transverse_rebar,
)
from sp63_core.report import CalculationProtocol, build_calculation_protocol
from sp63_core.sections.rectangular import RectangularSection

DesignStatus = Literal["pass", "fail", "review_or_fail"]


@dataclass(frozen=True)
class RectangularDesignResult:
    """Result of deterministic rectangular element reinforcement design."""

    section: RectangularSection
    concrete: Concrete
    longitudinal_rebar: Rebar
    transverse_rebar: Rebar
    M: float
    Q: float
    longitudinal_options: tuple[LongitudinalRebarOption, ...]
    selected_longitudinal: LongitudinalRebarOption | None
    transverse_options: tuple[TransverseRebarOption, ...]
    selected_transverse: TransverseRebarOption | None
    protocol: CalculationProtocol | None
    status: DesignStatus
    warnings: tuple[str, ...]
    requires_engineer_review: bool = True


def design_rectangular_element(
    section: RectangularSection,
    concrete: Concrete,
    longitudinal_rebar: Rebar,
    transverse_rebar: Rebar,
    M: float,
    Q: float,
    *,
    longitudinal_max_results: int = 5,
    transverse_max_results: int = 5,
) -> RectangularDesignResult:
    """Select passing longitudinal and transverse reinforcement and protocol it."""
    if M < 0:
        raise ValueError("M must be non-negative")
    if Q < 0:
        raise ValueError("Q must be non-negative")

    longitudinal_options = select_longitudinal_rebar(
        section=section,
        concrete=concrete,
        rebar=longitudinal_rebar,
        M=M,
        max_results=longitudinal_max_results,
    )
    if not longitudinal_options:
        return RectangularDesignResult(
            section=section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            transverse_rebar=transverse_rebar,
            M=M,
            Q=Q,
            longitudinal_options=(),
            selected_longitudinal=None,
            transverse_options=(),
            selected_transverse=None,
            protocol=None,
            status="fail",
            warnings=("no passing longitudinal reinforcement options",),
            requires_engineer_review=True,
        )

    selected_longitudinal = longitudinal_options[0]
    transverse_options = select_transverse_rebar(
        section=selected_longitudinal.section,
        concrete=concrete,
        stirrup_rebar=transverse_rebar,
        Q=Q,
        max_results=transverse_max_results,
    )
    if not transverse_options:
        return RectangularDesignResult(
            section=section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            transverse_rebar=transverse_rebar,
            M=M,
            Q=Q,
            longitudinal_options=longitudinal_options,
            selected_longitudinal=selected_longitudinal,
            transverse_options=(),
            selected_transverse=None,
            protocol=None,
            status="fail",
            warnings=("no passing transverse reinforcement options",),
            requires_engineer_review=True,
        )

    selected_transverse = transverse_options[0]
    protocol = build_calculation_protocol(
        input_data={
            "M": M,
            "Q": Q,
            "units": "N, mm, MPa",
        },
        materials={
            "concrete": concrete.model_dump(),
            "longitudinal_rebar": longitudinal_rebar.model_dump(),
            "transverse_rebar": transverse_rebar.model_dump(),
        },
        geometry={
            "b": selected_longitudinal.section.b,
            "h": selected_longitudinal.section.h,
            "h0": selected_longitudinal.section.effective_depth(),
            "cover": selected_longitudinal.section.cover,
            "stirrup_diameter": selected_longitudinal.section.stirrup_diameter,
            "main_bar_diameter": selected_longitudinal.section.main_bar_diameter,
            "compression_bar_diameter": (
                selected_longitudinal.section.compression_bar_diameter
            ),
        },
        reinforcement={
            "longitudinal": {
                "scheme": selected_longitudinal.scheme,
                "bar_count": selected_longitudinal.bar_count,
                "diameter": selected_longitudinal.diameter,
                "As": selected_longitudinal.As,
            },
            "transverse": {
                "scheme": selected_transverse.scheme,
                "diameter": selected_transverse.diameter,
                "legs": selected_transverse.legs,
                "spacing": selected_transverse.spacing,
                "Asw": selected_transverse.Asw,
            },
        },
        checks={
            "bending": selected_longitudinal.bending,
            "shear": selected_transverse.shear,
        },
    )

    return RectangularDesignResult(
        section=section,
        concrete=concrete,
        longitudinal_rebar=longitudinal_rebar,
        transverse_rebar=transverse_rebar,
        M=M,
        Q=Q,
        longitudinal_options=longitudinal_options,
        selected_longitudinal=selected_longitudinal,
        transverse_options=transverse_options,
        selected_transverse=selected_transverse,
        protocol=protocol,
        status=protocol.status,
        warnings=protocol.warnings,
        requires_engineer_review=True,
    )
