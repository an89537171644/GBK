"""End-to-end rectangular reinforced concrete element design."""

from dataclasses import dataclass

from sp63_core.materials import (
    LONGITUDINAL_DIAMETERS,
    STIRRUP_DIAMETERS,
    Concrete,
    LoadDuration,
    Rebar,
    get_concrete,
    get_rebar,
)
from sp63_core.rebar import (
    LongitudinalRebarOption,
    TransverseRebarOption,
    select_longitudinal_rebar,
    select_transverse_rebar,
)
from sp63_core.rebar.longitudinal import DEFAULT_BAR_COUNTS
from sp63_core.rebar.transverse import DEFAULT_STIRRUP_LEGS, DEFAULT_STIRRUP_SPACINGS
from sp63_core.report import CalculationProtocol, build_calculation_protocol
from sp63_core.sections import RectangularSection


@dataclass(frozen=True)
class RectangularDesignInput:
    """Input data for draft end-to-end rectangular element design."""

    b: float
    h: float
    cover: float
    stirrup_diameter_for_geometry: float
    concrete_class: str
    longitudinal_rebar_class: str
    stirrup_rebar_class: str
    M: float
    Q: float
    load_duration: LoadDuration = "short"
    main_bar_counts: tuple[int, ...] = DEFAULT_BAR_COUNTS
    main_bar_diameters: tuple[int, ...] = LONGITUDINAL_DIAMETERS
    stirrup_diameters: tuple[int, ...] = STIRRUP_DIAMETERS
    stirrup_legs_options: tuple[int, ...] = DEFAULT_STIRRUP_LEGS
    stirrup_spacings: tuple[int, ...] = DEFAULT_STIRRUP_SPACINGS
    max_longitudinal_options: int = 5
    max_transverse_options: int = 5
    min_clear_spacing: float = 25.0


@dataclass(frozen=True)
class RectangularDesignResult:
    """Result of draft end-to-end rectangular element design."""

    input_data: RectangularDesignInput
    section: RectangularSection
    concrete: Concrete
    longitudinal_rebar: Rebar
    stirrup_rebar: Rebar
    longitudinal_options: tuple[LongitudinalRebarOption, ...]
    selected_longitudinal: LongitudinalRebarOption | None
    transverse_options: tuple[TransverseRebarOption, ...]
    selected_transverse: TransverseRebarOption | None
    protocol: CalculationProtocol | None
    status: str
    warnings: tuple[str, ...]
    requires_engineer_review: bool = True


def design_rectangular_element(input_data: RectangularDesignInput) -> RectangularDesignResult:
    """Design a rectangular element using existing draft selection and check modules."""
    base_section = RectangularSection(
        b=input_data.b,
        h=input_data.h,
        cover=input_data.cover,
        stirrup_diameter=input_data.stirrup_diameter_for_geometry,
        main_bar_diameter=20,
    )
    concrete = get_concrete(input_data.concrete_class)
    longitudinal_rebar = get_rebar(input_data.longitudinal_rebar_class)
    stirrup_rebar = get_rebar(input_data.stirrup_rebar_class)

    longitudinal_options = select_longitudinal_rebar(
        section=base_section,
        concrete=concrete,
        rebar=longitudinal_rebar,
        M=input_data.M,
        bar_counts=input_data.main_bar_counts,
        diameters=input_data.main_bar_diameters,
        max_results=input_data.max_longitudinal_options,
        load_duration=input_data.load_duration,
        min_clear_spacing=input_data.min_clear_spacing,
    )
    if not longitudinal_options:
        return RectangularDesignResult(
            input_data=input_data,
            section=base_section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            stirrup_rebar=stirrup_rebar,
            longitudinal_options=(),
            selected_longitudinal=None,
            transverse_options=(),
            selected_transverse=None,
            protocol=None,
            status="fail",
            warnings=("no passing longitudinal reinforcement options",),
        )

    selected_longitudinal = longitudinal_options[0]
    transverse_options = select_transverse_rebar(
        section=selected_longitudinal.section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=input_data.Q,
        diameters=input_data.stirrup_diameters,
        legs_options=input_data.stirrup_legs_options,
        spacings=input_data.stirrup_spacings,
        max_results=input_data.max_transverse_options,
    )
    if not transverse_options:
        return RectangularDesignResult(
            input_data=input_data,
            section=base_section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            stirrup_rebar=stirrup_rebar,
            longitudinal_options=longitudinal_options,
            selected_longitudinal=selected_longitudinal,
            transverse_options=(),
            selected_transverse=None,
            protocol=None,
            status="fail",
            warnings=(
                *selected_longitudinal.warnings,
                "no passing transverse reinforcement options",
            ),
        )

    selected_transverse = transverse_options[0]
    longitudinal_constructive_values = selected_longitudinal.constructive.intermediate_values
    constructive_values = selected_transverse.constructive.intermediate_values
    shear_values = selected_transverse.shear.intermediate_values
    protocol = build_calculation_protocol(
        input_data={
            "M": input_data.M,
            "Q": input_data.Q,
            "load_duration": input_data.load_duration,
        },
        materials={
            "concrete_class": concrete.class_name,
            "longitudinal_rebar_class": longitudinal_rebar.class_name,
            "stirrup_rebar_class": stirrup_rebar.class_name,
        },
        geometry={
            "b": input_data.b,
            "h": input_data.h,
            "h0": selected_longitudinal.section.effective_depth(),
            "cover": input_data.cover,
            "stirrup_diameter_for_geometry": input_data.stirrup_diameter_for_geometry,
        },
        reinforcement={
            "main": selected_longitudinal.scheme,
            "As": selected_longitudinal.As,
            "longitudinal_constructive_status": selected_longitudinal.constructive.status,
            "longitudinal_reinforcement_ratio_percent": longitudinal_constructive_values[
                "reinforcement_ratio_percent"
            ],
            "stirrups": selected_transverse.scheme,
            "Asw": selected_transverse.Asw,
            "sw": selected_transverse.spacing,
            "legs": selected_transverse.legs,
            "stirrup_constructive_status": selected_transverse.constructive.status,
            "stirrup_constructive_max_spacing": constructive_values["max_spacing"],
            "stirrup_steel_consumption": selected_transverse.steel_consumption,
            "stirrup_sw_max_by_shear_rule": shear_values["sw_max_by_shear_rule"],
            "stirrup_qsw_rule_status": shear_values["qsw_rule_status"],
            "stirrup_transverse_reinforcement_countable": shear_values[
                "transverse_reinforcement_countable"
            ],
        },
        checks={
            "bending": selected_longitudinal.bending,
            "shear": selected_transverse.shear,
        },
    )
    status = "pass" if protocol.status == "pass" else protocol.status
    warnings = (
        *selected_longitudinal.warnings,
        *selected_transverse.warnings,
        *protocol.warnings,
    )

    return RectangularDesignResult(
        input_data=input_data,
        section=base_section,
        concrete=concrete,
        longitudinal_rebar=longitudinal_rebar,
        stirrup_rebar=stirrup_rebar,
        longitudinal_options=longitudinal_options,
        selected_longitudinal=selected_longitudinal,
        transverse_options=transverse_options,
        selected_transverse=selected_transverse,
        protocol=protocol,
        status=status,
        warnings=warnings,
    )
