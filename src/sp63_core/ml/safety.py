"""Draft deterministic safety wrapper for ML predictions."""

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from sp63_core.checks import check_bending_rectangular, check_shear_rectangular
from sp63_core.dataset import DatasetCase
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.ml.proposal import MLReinforcementProposal, proposal_from_prediction
from sp63_core.rebar import (
    check_longitudinal_constructive,
    check_single_layer_layout,
    check_transverse_constructive,
)
from sp63_core.rebar.transverse import QSW_MIN_RULE_WARNING, SHEAR_RULE_MAX_WARNING
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

ADVISORY_WARNING = (
    "draft ML safety gate: baseline ML is advisory only; deterministic SP63 checks "
    "remain mandatory"
)
NARROW_ACCEPTANCE_WARNING = (
    "accepted_by_deterministic_core covers only the narrow checked scope; "
    "project use remains prohibited"
)
LONG_DURATION_UNSUPPORTED_WARNING = (
    "ML proposal rejected: load_duration='long' is unsupported until the "
    "deterministic shear load-combination context is implemented"
)


def check_ml_proposal_safety(
    proposal: MLReinforcementProposal,
    original_case: DatasetCase,
) -> dict[str, Any]:
    """Run deterministic checks for the exact ML reinforcement proposal."""
    if original_case.load_duration == "long":
        return _unsupported_long_duration_result(proposal, original_case)

    orientation = RectangularBendingOrientation(
        local_axes_id=original_case.local_axes_id,
        moment_axis=original_case.moment_axis,
        tension_face=original_case.tension_face,
    )
    section = RectangularSection(
        b=original_case.b,
        h=original_case.h,
        cover=original_case.cover,
        stirrup_diameter=proposal.stirrup_diameter,
        main_bar_diameter=proposal.main_bar_diameter,
    )
    concrete = get_concrete(original_case.concrete_class)
    longitudinal_rebar = get_rebar(original_case.rebar_class)
    stirrup_rebar = get_rebar(original_case.stirrup_class)
    As = proposal.main_bar_count * area_by_diameter(proposal.main_bar_diameter)
    Asw = proposal.stirrup_legs * area_by_diameter(proposal.stirrup_diameter)

    layout = check_single_layer_layout(
        section=section,
        bar_count=proposal.main_bar_count,
        diameter=proposal.main_bar_diameter,
    )
    longitudinal_constructive = check_longitudinal_constructive(
        section=section,
        bar_count=proposal.main_bar_count,
        As=As,
        element_type="beam",
    )
    bending = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=longitudinal_rebar,
        As=As,
        M=original_case.M,
        orientation=orientation,
        load_duration=original_case.load_duration,
    )
    shear = check_shear_rectangular(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=original_case.Q,
        Asw=Asw,
        sw=proposal.stirrup_spacing,
    )
    transverse_constructive = check_transverse_constructive(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=original_case.Q,
        stirrup_diameter=proposal.stirrup_diameter,
        Asw=Asw,
        spacing=proposal.stirrup_spacing,
        element_type="beam",
    )

    blocking_shear_warnings = _has_blocking_shear_warning(shear.warnings)
    accepted_by_deterministic_core = (
        layout.layout_feasible
        and longitudinal_constructive.status == "pass"
        and bending.status == "pass"
        and shear.status == "pass"
        and transverse_constructive.status in ("pass", "warning")
        and not blocking_shear_warnings
    )
    warnings = (
        ADVISORY_WARNING,
        NARROW_ACCEPTANCE_WARNING,
        *layout.warnings,
        *longitudinal_constructive.warnings,
        *bending.warnings,
        *shear.warnings,
        *transverse_constructive.warnings,
    )

    return {
        "ml_is_advisory": True,
        "accepted_by_deterministic_core": accepted_by_deterministic_core,
        "bending_status": bending.status,
        "shear_status": shear.status,
        "layout_feasible": layout.layout_feasible,
        "longitudinal_constructive_status": longitudinal_constructive.status,
        "transverse_constructive_status": transverse_constructive.status,
        "stirrup_diameter_mode": "geometry_input_parameter",
        "local_axes_id": original_case.local_axes_id,
        "moment_axis": original_case.moment_axis,
        "tension_face": original_case.tension_face,
        "load_duration": original_case.load_duration,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
        "warnings": warnings,
        "proposal": asdict(proposal),
    }


def check_ml_prediction_safety(
    prediction: Mapping[str, Any],
    original_case: DatasetCase,
) -> dict[str, Any]:
    """Backward-compatible wrapper around proposal reconstruction and safety."""
    proposal, proposal_warnings = proposal_from_prediction(
        prediction,
        geometry_stirrup_diameter=original_case.geometry_stirrup_diameter,
    )
    result = check_ml_proposal_safety(proposal, original_case)
    result["warnings"] = (*proposal_warnings, *result["warnings"])
    result["prediction_keys"] = tuple(sorted(prediction))
    return result


def _unsupported_long_duration_result(
    proposal: MLReinforcementProposal,
    original_case: DatasetCase,
) -> dict[str, Any]:
    return {
        "ml_is_advisory": True,
        "accepted_by_deterministic_core": False,
        "bending_status": "not_checked",
        "shear_status": "not_checked",
        "layout_feasible": False,
        "longitudinal_constructive_status": "not_checked",
        "transverse_constructive_status": "not_checked",
        "stirrup_diameter_mode": "geometry_input_parameter",
        "local_axes_id": original_case.local_axes_id,
        "moment_axis": original_case.moment_axis,
        "tension_face": original_case.tension_face,
        "load_duration": original_case.load_duration,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "requires_engineer_review": True,
        "rejection_reasons": (LONG_DURATION_UNSUPPORTED_WARNING,),
        "warnings": (
            ADVISORY_WARNING,
            NARROW_ACCEPTANCE_WARNING,
            LONG_DURATION_UNSUPPORTED_WARNING,
        ),
        "proposal": asdict(proposal),
    }


def _has_blocking_shear_warning(warnings: tuple[str, ...]) -> bool:
    return SHEAR_RULE_MAX_WARNING in warnings or QSW_MIN_RULE_WARNING in warnings
