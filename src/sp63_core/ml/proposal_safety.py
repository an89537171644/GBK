"""Safety wrapper for advisory ML proposals verified by deterministic checks."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

from sp63_core.checks import (
    check_bending_rectangular,
    check_curvature_deflection_rectangular,
    check_normal_crack_formation_rectangular,
    check_normal_crack_width_rectangular,
    check_shear_rectangular,
)
from sp63_core.materials import area_by_diameter, get_concrete, get_rebar
from sp63_core.rebar import (
    check_longitudinal_constructive,
    check_single_layer_layout,
    check_transverse_constructive,
)
from sp63_core.rebar.transverse import QSW_MIN_RULE_WARNING, SHEAR_RULE_MAX_WARNING
from sp63_core.report import build_calculation_protocol
from sp63_core.sections import RectangularBendingOrientation, RectangularSection

ML_PROPOSAL_WARNINGS: tuple[str, ...] = (
    "ML proposal is advisory-only",
    "deterministic SP63 verification is mandatory",
    "accepted result still requires engineer review",
    "accepted means only the narrow deterministic checks; project use is prohibited",
)


@dataclass(frozen=True)
class MLProposal:
    """Raw advisory ML proposal to be checked by deterministic SP63 core."""

    proposal_id: str
    proposal_type: str
    input_data: dict[str, Any]
    proposed_values: dict[str, Any]
    model_name: str
    model_kind: str
    ml_is_advisory_only: bool = True
    requires_engineer_review: bool = True


@dataclass(frozen=True)
class MLProposalVerificationResult:
    """Deterministic verification result for one advisory ML proposal."""

    proposal_id: str
    accepted: bool
    verification_status: str
    deterministic_strength_status: str
    deterministic_serviceability_status: str
    deterministic_overall_status: str
    layout_feasible: bool | None
    longitudinal_constructive_status: str
    transverse_constructive_status: str
    rejection_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    deterministic_checks_required: bool = True
    ml_is_advisory_only: bool = True
    requires_engineer_review: bool = True


def verify_ml_proposal_with_deterministic_core(
    proposal: MLProposal,
) -> MLProposalVerificationResult:
    """Verify an advisory ML proposal using deterministic SP63 checks."""
    if proposal.proposal_type != "rectangular_rebar_scheme":
        return _rejected_result(
            proposal,
            reason=f"unsupported proposal_type {proposal.proposal_type!r}",
            strength_status="not_checked",
            serviceability_status="not_checked",
            overall_status="review_or_fail",
        )

    input_data = proposal.input_data
    proposed = proposal.proposed_values
    orientation = RectangularBendingOrientation(
        local_axes_id=_required_string(input_data, "local_axes_id"),
        moment_axis=_required_string(input_data, "moment_axis"),
        tension_face=_required_string(input_data, "tension_face"),
    )
    load_duration = _required_string(input_data, "load_duration")
    if load_duration not in ("short", "long"):
        raise ValueError("load_duration must be 'short' or 'long'")
    if load_duration == "long":
        return _rejected_result(
            proposal,
            reason=(
                "load_duration='long' is unsupported until the deterministic "
                "shear load-combination context is implemented"
            ),
            strength_status="not_checked",
            serviceability_status="not_checked",
            overall_status="review_or_fail",
        )

    main_bar_count = _positive_int(proposed, "main_bar_count")
    main_bar_diameter = _positive_float(proposed, "main_bar_diameter")
    stirrup_diameter = _positive_float(proposed, "stirrup_diameter")
    stirrup_legs = _positive_int(proposed, "stirrup_legs")
    stirrup_spacing = _positive_float(proposed, "stirrup_spacing")

    section = RectangularSection(
        b=_positive_float(input_data, "b"),
        h=_positive_float(input_data, "h"),
        cover=_positive_float(input_data, "cover"),
        stirrup_diameter=stirrup_diameter,
        main_bar_diameter=main_bar_diameter,
    )
    # Preserve the caller's geometry input in the protocol while verifying the
    # actual proposed stirrup diameter in the deterministic section.
    if "stirrup_diameter_for_geometry" not in input_data:
        raise ValueError("input_data is missing required field 'stirrup_diameter_for_geometry'")
    section.validate_geometry()

    concrete = get_concrete(str(input_data["concrete_class"]))
    longitudinal_rebar = get_rebar(str(input_data["longitudinal_rebar_class"]))
    stirrup_rebar = get_rebar(str(input_data["stirrup_rebar_class"]))
    M = _nonnegative_float(input_data, "M")
    Q = _nonnegative_float(input_data, "Q")
    As = main_bar_count * area_by_diameter(main_bar_diameter)
    Asw = stirrup_legs * area_by_diameter(stirrup_diameter)

    layout = check_single_layer_layout(
        section=section,
        bar_count=main_bar_count,
        diameter=main_bar_diameter,
    )
    longitudinal_constructive = check_longitudinal_constructive(
        section=section,
        bar_count=main_bar_count,
        As=As,
        element_type="beam",
    )

    bending = check_bending_rectangular(
        section=section,
        concrete=concrete,
        rebar=longitudinal_rebar,
        As=As,
        M=M,
        orientation=orientation,
        load_duration=load_duration,
    )
    shear = check_shear_rectangular(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=Q,
        Asw=Asw,
        sw=stirrup_spacing,
    )
    transverse_constructive = check_transverse_constructive(
        section=section,
        concrete=concrete,
        stirrup_rebar=stirrup_rebar,
        Q=Q,
        stirrup_diameter=stirrup_diameter,
        Asw=Asw,
        spacing=stirrup_spacing,
        element_type="beam",
    )
    blocking_shear_warnings = any(
        warning in (QSW_MIN_RULE_WARNING, SHEAR_RULE_MAX_WARNING)
        for warning in shear.warnings
    )
    checks: dict[str, Any] = {
        "bending": bending,
        "shear": shear,
    }

    Mser = _optional_nonnegative_float(input_data, "Mser")
    if Mser is not None:
        crack_formation = check_normal_crack_formation_rectangular(
            section=section,
            concrete=concrete,
            Mser=Mser,
        )
        checks["crack_formation"] = crack_formation
        checks["crack_width"] = check_normal_crack_width_rectangular(
            section=section,
            concrete=concrete,
            rebar=longitudinal_rebar,
            Mser=Mser,
            As=As,
            main_bar_diameter=main_bar_diameter,
            crack_formation=crack_formation,
        )
        span = _optional_nonnegative_float(input_data, "span")
        if span is not None and span > 0:
            checks["deflection"] = check_curvature_deflection_rectangular(
                section=section,
                concrete=concrete,
                rebar=longitudinal_rebar,
                Mser=Mser,
                As=As,
                span=span,
                crack_formation=crack_formation,
            )

    protocol = build_calculation_protocol(
        input_data=input_data,
        materials={
            "concrete_class": concrete.class_name,
            "longitudinal_rebar_class": longitudinal_rebar.class_name,
            "stirrup_rebar_class": stirrup_rebar.class_name,
        },
        geometry={
            "b": section.b,
            "h": section.h,
            "cover": section.cover,
            "h0": section.effective_depth(),
        },
        reinforcement={
            "main_bar_count": main_bar_count,
            "main_bar_diameter": main_bar_diameter,
            "stirrup_diameter": stirrup_diameter,
            "stirrup_legs": stirrup_legs,
            "stirrup_spacing": stirrup_spacing,
            "As": As,
            "Asw": Asw,
        },
        checks=checks,
    )
    accepted = (
        protocol.strength_status == "pass"
        and protocol.serviceability_status in ("pass", "not_checked")
        and protocol.overall_status == "pass"
        and layout.layout_feasible
        and longitudinal_constructive.status == "pass"
        and transverse_constructive.status in ("pass", "warning")
        and not blocking_shear_warnings
    )
    rejection_reasons = list(_rejection_reasons(protocol.checks))
    if not layout.layout_feasible:
        rejection_reasons.append("single-layer longitudinal layout is not feasible")
    if longitudinal_constructive.status != "pass":
        rejection_reasons.append("longitudinal constructive check failed")
    if transverse_constructive.status not in ("pass", "warning"):
        rejection_reasons.append("transverse constructive check failed")
    if blocking_shear_warnings:
        rejection_reasons.append("blocking shear warning prevents acceptance")
    if not accepted and not rejection_reasons:
        rejection_reasons = [
            f"deterministic strength status is {protocol.strength_status}",
            f"deterministic serviceability status is {protocol.serviceability_status}",
            f"deterministic overall status is {protocol.overall_status}",
        ]
    warnings = tuple(
        dict.fromkeys(
            (
                *ML_PROPOSAL_WARNINGS,
                *layout.warnings,
                *longitudinal_constructive.warnings,
                *shear.warnings,
                *transverse_constructive.warnings,
                *protocol.warnings,
            )
        )
    )
    if not accepted:
        warnings = (
            *warnings,
            "ML proposal rejected by deterministic SP63 verification",
        )
    return MLProposalVerificationResult(
        proposal_id=proposal.proposal_id,
        accepted=accepted,
        verification_status="accepted" if accepted else "rejected",
        deterministic_strength_status=protocol.strength_status,
        deterministic_serviceability_status=protocol.serviceability_status,
        deterministic_overall_status=protocol.overall_status,
        layout_feasible=layout.layout_feasible,
        longitudinal_constructive_status=longitudinal_constructive.status,
        transverse_constructive_status=transverse_constructive.status,
        rejection_reasons=() if accepted else tuple(rejection_reasons),
        warnings=warnings,
    )


def _rejected_result(
    proposal: MLProposal,
    *,
    reason: str,
    strength_status: str,
    serviceability_status: str,
    overall_status: str,
) -> MLProposalVerificationResult:
    return MLProposalVerificationResult(
        proposal_id=proposal.proposal_id,
        accepted=False,
        verification_status="rejected",
        deterministic_strength_status=strength_status,
        deterministic_serviceability_status=serviceability_status,
        deterministic_overall_status=overall_status,
        layout_feasible=None,
        longitudinal_constructive_status="not_checked",
        transverse_constructive_status="not_checked",
        rejection_reasons=(reason,),
        warnings=(
            *ML_PROPOSAL_WARNINGS,
            "ML proposal rejected by deterministic SP63 verification",
        ),
    )


def _rejection_reasons(checks: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    reasons: list[str] = []
    for check_name, check in checks.items():
        status = check.get("status")
        if status == "fail":
            reasons.append(f"{check_name} check failed")
        elif status == "outside_applicability":
            reasons.append(f"{check_name} check is outside applicability")
    return tuple(reasons)


def _positive_float(values: Mapping[str, Any], key: str) -> float:
    if key not in values:
        raise ValueError(f"missing required field {key!r}")
    value = float(values[key])
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{key} must be finite and positive")
    return value


def _required_string(values: Mapping[str, Any], key: str) -> str:
    if key not in values:
        raise ValueError(f"missing required field {key!r}")
    value = values[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _positive_int(values: Mapping[str, Any], key: str) -> int:
    value = int(round(_positive_float(values, key)))
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _nonnegative_float(values: Mapping[str, Any], key: str) -> float:
    if key not in values:
        raise ValueError(f"missing required field {key!r}")
    value = float(values[key])
    if not isfinite(value) or value < 0:
        raise ValueError(f"{key} must be finite and nonnegative")
    return value


def _optional_nonnegative_float(values: Mapping[str, Any], key: str) -> float | None:
    if key not in values or values[key] is None:
        return None
    value = float(values[key])
    if not isfinite(value) or value < 0:
        raise ValueError(f"{key} must be finite and nonnegative")
    return value
