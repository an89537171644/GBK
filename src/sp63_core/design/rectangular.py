"""End-to-end rectangular reinforced concrete element design."""

from dataclasses import dataclass

from sp63_core.checks import (
    CrackFormationResult,
    CrackWidthResult,
    DeflectionResult,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
)
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
    Mser: float | None = None
    check_cracks: bool = False
    check_crack_width: bool = False
    acrc_limit: float = 0.3
    check_deflection: bool = False
    span: float | None = None
    deflection_limit: float | None = None
    deflection_limit_ratio: float = 250.0
    deflection_loading_scheme: str = "simply_supported_uniform"


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
    crack_formation: CrackFormationResult | None
    crack_width: CrackWidthResult | None
    deflection: DeflectionResult | None
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
            crack_formation=None,
            crack_width=None,
            deflection=None,
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
            crack_formation=None,
            crack_width=None,
            deflection=None,
            protocol=None,
            status="fail",
            warnings=(
                *selected_longitudinal.warnings,
                "no passing transverse reinforcement options",
            ),
        )

    selected_transverse = transverse_options[0]
    service_moment = input_data.M if input_data.Mser is None else input_data.Mser
    crack_formation = None
    if input_data.check_cracks or input_data.check_crack_width or input_data.check_deflection:
        crack_formation = check_normal_crack_formation_rectangular(
            section=selected_longitudinal.section,
            concrete=concrete,
            Mser=service_moment,
        )
    crack_width = None
    if input_data.check_crack_width:
        crack_width = check_normal_crack_width_rectangular(
            section=selected_longitudinal.section,
            concrete=concrete,
            rebar=longitudinal_rebar,
            Mser=service_moment,
            As=selected_longitudinal.As,
            main_bar_diameter=selected_longitudinal.section.main_bar_diameter,
            acrc_limit=input_data.acrc_limit,
            crack_formation=crack_formation,
        )
    deflection = None
    if input_data.check_deflection:
        if input_data.span is None:
            raise ValueError("span must be provided when check_deflection is True")
        if input_data.span <= 0:
            raise ValueError("span must be positive")
        deflection = check_curvature_deflection_rectangular(
            section=selected_longitudinal.section,
            concrete=concrete,
            rebar=longitudinal_rebar,
            Mser=service_moment,
            As=selected_longitudinal.As,
            span=input_data.span,
            deflection_limit=input_data.deflection_limit,
            deflection_limit_ratio=input_data.deflection_limit_ratio,
            loading_scheme=input_data.deflection_loading_scheme,
            crack_formation=crack_formation,
        )

    longitudinal_constructive_values = selected_longitudinal.constructive.intermediate_values
    constructive_values = selected_transverse.constructive.intermediate_values
    shear_values = selected_transverse.shear.intermediate_values
    checks = {
        "bending": selected_longitudinal.bending,
        "shear": selected_transverse.shear,
    }
    if crack_formation is not None:
        checks["crack_formation"] = crack_formation
    if crack_width is not None:
        checks["crack_width"] = crack_width
    if deflection is not None:
        checks["deflection"] = deflection

    protocol = build_calculation_protocol(
        input_data={
            "M": input_data.M,
            "Q": input_data.Q,
            "Mser": (
                service_moment
                if input_data.check_cracks
                or input_data.check_crack_width
                or input_data.check_deflection
                else input_data.Mser
            ),
            "check_cracks": input_data.check_cracks,
            "check_crack_width": input_data.check_crack_width,
            "acrc_limit": input_data.acrc_limit,
            "check_deflection": input_data.check_deflection,
            "span": input_data.span,
            "deflection_limit": input_data.deflection_limit,
            "deflection_limit_ratio": input_data.deflection_limit_ratio,
            "deflection_loading_scheme": input_data.deflection_loading_scheme,
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
        checks=checks,
    )
    strength_passed = (
        selected_longitudinal.bending.status == "pass"
        and selected_transverse.shear.status == "pass"
    )
    status = "pass" if strength_passed else protocol.status
    warnings = [
        *selected_longitudinal.warnings,
        *selected_transverse.warnings,
        *protocol.warnings,
    ]
    if (
        crack_formation is not None
        and crack_formation.status == "crack"
        and crack_width is None
    ):
        warnings.append("normal cracks are expected; crack width check is required")
    if crack_width is not None and crack_width.status == "fail":
        warnings.append("crack width exceeds draft limit; serviceability review is required")
    if deflection is not None and deflection.status == "fail":
        warnings.append("deflection exceeds draft limit; serviceability review is required")

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
        crack_formation=crack_formation,
        crack_width=crack_width,
        deflection=deflection,
        protocol=protocol,
        status=status,
        warnings=tuple(warnings),
    )
