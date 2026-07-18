"""End-to-end rectangular reinforced concrete element design."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal

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
    UnsupportedULSMaterialProfileError,
    get_concrete,
    get_rebar,
    resolve_uls_material_context,
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
from sp63_core.sections import RectangularBendingOrientation, RectangularSection
from sp63_core.sections.orientation import MomentAxis, TensionFace


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
    local_axes_id: str
    moment_axis: MomentAxis
    tension_face: TensionFace
    load_duration: LoadDuration
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

    def bending_orientation(self) -> RectangularBendingOrientation:
        """Build and validate the mandatory local-axis contract."""
        return RectangularBendingOrientation(
            local_axes_id=self.local_axes_id,
            moment_axis=self.moment_axis,
            tension_face=self.tension_face,
        )


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
    strength_status: str
    serviceability_status: str
    overall_status: str
    status: str
    warnings: tuple[str, ...]
    status_scope: str = "public"
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    requires_engineer_review: bool = True


def design_rectangular_element(
    input_data: RectangularDesignInput,
    *,
    status_scope: Literal["public", "diagnostic"] = "public",
) -> RectangularDesignResult:
    """Design a rectangular element using existing draft selection and check modules.

    The public scope applies all unresolved engineering gates. The diagnostic
    scope is reserved for regression and review artifacts and never changes
    the project-use prohibition.
    """
    if status_scope not in ("public", "diagnostic"):
        raise ValueError("status_scope must be 'public' or 'diagnostic'")
    orientation = input_data.bending_orientation()
    for name, value in (("M", input_data.M), ("Q", input_data.Q)):
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite non-negative value")
    base_section = RectangularSection(
        b=input_data.b,
        h=input_data.h,
        cover=input_data.cover,
        stirrup_diameter=input_data.stirrup_diameter_for_geometry,
        main_bar_diameter=20,
    )
    base_section.validate_geometry()
    concrete = get_concrete(input_data.concrete_class)
    longitudinal_rebar = get_rebar(input_data.longitudinal_rebar_class)
    stirrup_rebar = get_rebar(input_data.stirrup_rebar_class)

    try:
        resolve_uls_material_context(
            concrete,
            longitudinal_rebar,
            input_data.load_duration,
        )
    except UnsupportedULSMaterialProfileError as exc:
        return _outside_applicability_result(
            input_data=input_data,
            section=base_section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            stirrup_rebar=stirrup_rebar,
            status_scope=status_scope,
            warning=f"{exc}; rectangular ULS design was not performed",
        )

    if input_data.load_duration == "long":
        return _outside_applicability_result(
            input_data=input_data,
            section=base_section,
            concrete=concrete,
            longitudinal_rebar=longitudinal_rebar,
            stirrup_rebar=stirrup_rebar,
            status_scope=status_scope,
            warning=(
                "long load context is verified for the isolated bending check only; "
                "concrete working-condition factors are not propagated to shear, so "
                "the end-to-end design is outside applicability"
            ),
        )

    longitudinal_options = select_longitudinal_rebar(
        section=base_section,
        concrete=concrete,
        rebar=longitudinal_rebar,
        M=input_data.M,
        orientation=orientation,
        load_duration=input_data.load_duration,
        bar_counts=input_data.main_bar_counts,
        diameters=input_data.main_bar_diameters,
        max_results=input_data.max_longitudinal_options,
        min_clear_spacing=input_data.min_clear_spacing,
    )
    if not longitudinal_options:
        no_option_status = (
            "fail" if status_scope == "diagnostic" else "outside_applicability"
        )
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
            strength_status=no_option_status,
            serviceability_status="not_checked",
            overall_status=no_option_status,
            status=no_option_status,
            warnings=(
                "no passing diagnostic longitudinal reinforcement options; "
                "public ULS bending remains outside applicability",
            ),
            status_scope=status_scope,
        )

    selected_longitudinal = longitudinal_options[0]
    geometry_stirrup_diameter = input_data.stirrup_diameter_for_geometry
    geometry_consistent_stirrup_diameters = tuple(
        diameter
        for diameter in input_data.stirrup_diameters
        if float(diameter) == float(geometry_stirrup_diameter)
    )
    if not geometry_consistent_stirrup_diameters:
        return RectangularDesignResult(
            input_data=input_data,
            section=selected_longitudinal.section,
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
            strength_status="outside_applicability",
            serviceability_status="not_checked",
            overall_status="outside_applicability",
            status="outside_applicability",
            warnings=(
                "no transverse candidate matches stirrup_diameter_for_geometry; "
                "h0 cannot be kept consistent",
            ),
            status_scope=status_scope,
        )
    transverse_options = select_transverse_rebar(
        section=selected_longitudinal.section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=input_data.Q,
        diameters=geometry_consistent_stirrup_diameters,
        legs_options=input_data.stirrup_legs_options,
        spacings=input_data.stirrup_spacings,
        max_results=input_data.max_transverse_options,
    )
    if not transverse_options:
        return RectangularDesignResult(
            input_data=input_data,
            section=selected_longitudinal.section,
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
            strength_status="fail",
            serviceability_status="not_checked",
            overall_status="fail",
            status="fail",
            warnings=(
                *selected_longitudinal.warnings,
                "no passing transverse reinforcement options",
            ),
            status_scope=status_scope,
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
    bending_values = selected_longitudinal.bending.intermediate_values
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
        status_scope=status_scope,
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
            "local_axes_id": input_data.local_axes_id,
            "moment_axis": input_data.moment_axis,
            "tension_face": input_data.tension_face,
            "moment_value_semantics": "non_negative_magnitude",
        },
        materials={
            "concrete_class": concrete.class_name,
            "longitudinal_rebar_class": longitudinal_rebar.class_name,
            "stirrup_rebar_class": stirrup_rebar.class_name,
            "normative_profile_id": bending_values["normative_profile_id"],
            "load_combination": bending_values["load_combination"],
            "Rb_base": bending_values["Rb_base"],
            "gamma_b1": bending_values["gamma_b1"],
            "Rb_effective": bending_values["Rb_effective"],
            "Rsc": bending_values["Rsc"],
        },
        geometry={
            "b": input_data.b,
            "h": input_data.h,
            "h0": selected_longitudinal.section.effective_depth(),
            "cover": input_data.cover,
            "cover_reference": bending_values["cover_reference"],
            "h0_source": bending_values["h0_source"],
            "stirrup_diameter_for_geometry": input_data.stirrup_diameter_for_geometry,
            "local_axes_id": input_data.local_axes_id,
            "moment_axis": input_data.moment_axis,
            "tension_face": input_data.tension_face,
            "compression_face": orientation.compression_face,
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
    strength_status = protocol.strength_status
    serviceability_status = protocol.serviceability_status
    overall_status = protocol.overall_status
    status = overall_status
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
        section=selected_longitudinal.section,
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
        strength_status=strength_status,
        serviceability_status=serviceability_status,
        overall_status=overall_status,
        status=status,
        warnings=tuple(warnings),
        status_scope=status_scope,
    )


def _outside_applicability_result(
    *,
    input_data: RectangularDesignInput,
    section: RectangularSection,
    concrete: Concrete,
    longitudinal_rebar: Rebar,
    stirrup_rebar: Rebar,
    status_scope: Literal["public", "diagnostic"],
    warning: str,
) -> RectangularDesignResult:
    """Build a fail-closed design result before any candidate enumeration."""
    return RectangularDesignResult(
        input_data=input_data,
        section=section,
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
        strength_status="outside_applicability",
        serviceability_status="not_checked",
        overall_status="outside_applicability",
        status="outside_applicability",
        warnings=(warning,),
        status_scope=status_scope,
    )
