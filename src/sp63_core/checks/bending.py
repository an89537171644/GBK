"""Rectangular bending section check for the SP 63 MVP.

Formula trace: ``docs/formulas/SP63_8_1_9_bending_rectangular.md``.

Units are N, N*mm, mm, MPa (N/mm2), and mm2. The implemented branch is
restricted to a singly reinforced rectangular section. Formula approval and
project use remain blocked pending independent engineering review.
"""

from dataclasses import dataclass, field
from math import inf, isfinite
from typing import Literal

from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import LoadDuration, Rebar
from sp63_core.materials.uls_context import (
    ULSMaterialContext,
    UnsupportedULSMaterialProfileError,
    resolve_uls_material_context,
)
from sp63_core.sections.orientation import RectangularBendingOrientation
from sp63_core.sections.rectangular import RectangularSection

BendingStatus = Literal["pass", "fail", "outside_applicability"]
EB2 = 0.0035
SOURCE_CLAUSE = (
    "SP 63.13330.2018 6.1.20; 8.1.4-8.1.6; 8.1.8-8.1.9; "
    "8.1.12 branch not implemented"
)
COVER_REFERENCE = "concrete_face_to_outer_stirrup_surface"


@dataclass(frozen=True)
class BendingResult:
    """Result of the restricted rectangular bending section check."""

    x: float | None
    xi: float | None
    xi_R: float | None
    Mult: float | None
    utilization: float | None
    status: BendingStatus
    capacity_applicable: bool
    diagnostic_Mult: float | None = None
    diagnostic_utilization: float | None = None
    diagnostic_status: BendingStatus = "outside_applicability"
    diagnostic_capacity_applicable: bool = False
    public_status: BendingStatus = "outside_applicability"
    status_scope: str = "public"
    capacity_publication_allowed: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)
    intermediate_values: dict[str, object] = field(default_factory=dict)
    source_clause: str = SOURCE_CLAUSE
    clause_8_1_3_status: str = "not_checked"
    clause_8_1_3_decision_status: str = "OPEN_QUESTION"
    completeness_status: str = "incomplete"
    evidence_status: str = "needs_engineer_review"
    project_use_status: str = "prohibited"
    project_use: bool = False
    layout_applicability_status: str = "not_checked_area_only"
    manual_applicability_confirmation_required: bool = True
    requires_engineer_review: bool = True


def check_bending_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    As: float,
    M: float,
    *,
    orientation: RectangularBendingOrientation,
    load_duration: LoadDuration,
    As_prime: float = 0.0,
) -> BendingResult:
    """Check the restricted provisional branch of ULS-BEND-RECT-001.

    ``M`` is a non-negative magnitude about ``orientation.moment_axis``. The
    tension face is never inferred from its sign. A numerical capacity is not
    formed outside the implemented applicability boundary.
    """
    if not isinstance(orientation, RectangularBendingOrientation):
        raise TypeError("orientation must be RectangularBendingOrientation")

    section.validate_geometry()
    b = section.b
    h0 = section.effective_depth()
    Rs = rebar.Rs
    Es = rebar.Es

    _validate_inputs(
        b=b,
        h0=h0,
        As=As,
        As_prime=As_prime,
        M=M,
        Rb=concrete.Rb,
        Rs=Rs,
        Es=Es,
    )

    try:
        material_context = resolve_uls_material_context(concrete, rebar, load_duration)
    except UnsupportedULSMaterialProfileError as exc:
        warning = f"{exc}; no bending capacity was calculated"
        return BendingResult(
            x=None,
            xi=None,
            xi_R=None,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=_unsupported_material_intermediate_values(
                section=section,
                orientation=orientation,
                concrete=concrete,
                rebar=rebar,
                As=As,
                As_prime=As_prime,
                M=M,
                load_duration=load_duration,
            ),
        )

    Rb = material_context.Rb_effective

    xi_R = 0.8 / (1.0 + (Rs / Es) / EB2)
    x_limit = xi_R * h0
    intermediate_values = _base_intermediate_values(
        section=section,
        orientation=orientation,
        material_context=material_context,
        As=As,
        As_prime=As_prime,
        M=M,
        Rs=Rs,
        Es=Es,
        h0=h0,
        xi_R=xi_R,
        x_limit=x_limit,
    )

    if As_prime != 0:
        warning = (
            "As_prime is outside ULS-BEND-RECT-001 v1 scope; "
            "no bending capacity was calculated"
        )
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "compression_reinforcement_outside_v1_scope",
            }
        )
        return BendingResult(
            x=None,
            xi=None,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )

    x = _compression_zone_height(Rs=Rs, As=As, Rb=Rb, b=b)
    if not isfinite(x):
        warning = (
            "derived compression zone height is non-finite; "
            "no bending capacity was calculated"
        )
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "non_finite_derived_compression_zone",
            }
        )
        return BendingResult(
            x=None,
            xi=None,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )
    xi = x / h0
    if not isfinite(xi):
        warning = (
            "derived relative compression zone height is non-finite; "
            "no bending capacity was calculated"
        )
        intermediate_values.update(
            {
                "x": x,
                "capacity_applicable": False,
                "applicability_reason": "non_finite_derived_relative_height",
            }
        )
        return BendingResult(
            x=x,
            xi=None,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )
    intermediate_values.update({"x": x, "xi": xi})

    if x <= 0:
        warning = "non-positive compression zone height; no bending capacity was calculated"
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "non_positive_compression_zone",
            }
        )
        return BendingResult(
            x=x,
            xi=xi,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )

    if x > x_limit:
        warning = (
            "compression zone height exceeds xi_R * h0; "
            "no bending capacity was calculated"
        )
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "compression_zone_exceeds_limit",
            }
        )
        return BendingResult(
            x=x,
            xi=xi,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )

    Mult = Rb * b * x * (h0 - 0.5 * x)
    if not isfinite(Mult) or Mult <= 0:
        warning = (
            "derived bending capacity is non-finite or non-positive; "
            "no bending capacity was published"
        )
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "invalid_derived_bending_capacity",
            }
        )
        return BendingResult(
            x=x,
            xi=xi,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )
    utilization = _utilization(M=M, Mult=Mult)
    if not isfinite(utilization):
        warning = (
            "derived bending utilization is non-finite; "
            "no bending capacity was published"
        )
        intermediate_values.update(
            {
                "capacity_applicable": False,
                "applicability_reason": "non_finite_derived_utilization",
            }
        )
        return BendingResult(
            x=x,
            xi=xi,
            xi_R=xi_R,
            Mult=None,
            utilization=None,
            status="outside_applicability",
            capacity_applicable=False,
            warnings=(warning,),
            intermediate_values=intermediate_values,
        )
    diagnostic_status: BendingStatus = "pass" if Mult >= M else "fail"
    warning = (
        "diagnostic arithmetic only: clause 8.1.3 is not checked; the public "
        "ULS result is outside applicability and capacity publication is prohibited"
    )
    intermediate_values.update(
        {
            "diagnostic_Mult": Mult,
            "diagnostic_utilization": utilization,
            "diagnostic_capacity_applicable": True,
            "capacity_applicable": False,
            "applicability_reason": "within_singly_reinforced_v1_scope",
            "diagnostic_status": diagnostic_status,
            "public_status": "outside_applicability",
            "status_scope": "diagnostic_arithmetic_only",
            "capacity_publication_allowed": False,
        }
    )
    return BendingResult(
        x=x,
        xi=xi,
        xi_R=xi_R,
        Mult=None,
        utilization=None,
        status="outside_applicability",
        capacity_applicable=False,
        diagnostic_Mult=Mult,
        diagnostic_utilization=utilization,
        diagnostic_status=diagnostic_status,
        diagnostic_capacity_applicable=True,
        status_scope="public",
        warnings=(warning,),
        intermediate_values=intermediate_values,
    )


def _base_intermediate_values(
    *,
    section: RectangularSection,
    orientation: RectangularBendingOrientation,
    material_context: ULSMaterialContext,
    As: float,
    As_prime: float,
    M: float,
    Rs: float,
    Es: float,
    h0: float,
    xi_R: float,
    x_limit: float,
) -> dict[str, object]:
    return {
        "b": section.b,
        "h": section.h,
        "cover": section.cover,
        "cover_reference": COVER_REFERENCE,
        "stirrup_diameter": section.stirrup_diameter,
        "main_bar_diameter": section.main_bar_diameter,
        "h0": h0,
        "h0_source": "derived_from_declared_geometry",
        "local_axes_id": orientation.local_axes_id,
        "moment_axis": orientation.moment_axis,
        "tension_face": orientation.tension_face,
        "compression_face": orientation.compression_face,
        "moment_value_semantics": "non_negative_magnitude",
        "Rb": material_context.Rb_effective,
        "Rb_base": material_context.Rb_base,
        "gamma_b1": material_context.gamma_b1,
        "Rb_effective": material_context.Rb_effective,
        "Rs": Rs,
        "Rsc": material_context.Rsc,
        "Es": Es,
        "load_duration": material_context.load_duration,
        "load_combination": material_context.load_combination,
        "normative_profile_id": material_context.normative_profile_id,
        "material_source_clauses": material_context.source_clauses,
        "As": As,
        "As_prime": As_prime,
        "M": M,
        "eb2": EB2,
        "xi_R": xi_R,
        "x_limit": x_limit,
        "source_clause": SOURCE_CLAUSE,
        "clause_8_1_3_status": "not_checked",
        "clause_8_1_3_decision_status": "OPEN_QUESTION",
        "public_status": "outside_applicability",
        "status_scope": "public",
        "capacity_publication_allowed": False,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "layout_applicability_status": "not_checked_area_only",
        "manual_applicability_confirmation_required": True,
        "requires_engineer_review": True,
    }


def _unsupported_material_intermediate_values(
    *,
    section: RectangularSection,
    orientation: RectangularBendingOrientation,
    concrete: Concrete,
    rebar: Rebar,
    As: float,
    As_prime: float,
    M: float,
    load_duration: object,
) -> dict[str, object]:
    """Return provenance without assigning an official profile to custom inputs."""
    return {
        "b": section.b,
        "h": section.h,
        "cover": section.cover,
        "cover_reference": COVER_REFERENCE,
        "stirrup_diameter": section.stirrup_diameter,
        "main_bar_diameter": section.main_bar_diameter,
        "h0": section.effective_depth(),
        "h0_source": "derived_from_declared_geometry",
        "local_axes_id": orientation.local_axes_id,
        "moment_axis": orientation.moment_axis,
        "tension_face": orientation.tension_face,
        "compression_face": orientation.compression_face,
        "moment_value_semantics": "non_negative_magnitude",
        "declared_concrete_class": concrete.class_name,
        "declared_rebar_class": rebar.class_name,
        "load_duration": load_duration,
        "As": As,
        "As_prime": As_prime,
        "M": M,
        "capacity_applicable": False,
        "applicability_reason": "unsupported_material_profile",
        "material_profile_status": "unsupported_or_not_catalog_matched",
        "normative_profile_id": None,
        "source_clause": SOURCE_CLAUSE,
        "clause_8_1_3_status": "not_checked",
        "clause_8_1_3_decision_status": "OPEN_QUESTION",
        "public_status": "outside_applicability",
        "status_scope": "public",
        "capacity_publication_allowed": False,
        "completeness_status": "incomplete",
        "evidence_status": "needs_engineer_review",
        "project_use_status": "prohibited",
        "project_use": False,
        "layout_applicability_status": "not_checked_area_only",
        "manual_applicability_confirmation_required": True,
        "requires_engineer_review": True,
    }


def _validate_inputs(
    *,
    b: float,
    h0: float,
    As: float,
    As_prime: float,
    M: float,
    Rb: float,
    Rs: float,
    Es: float,
) -> None:
    values = {
        "b": b,
        "h0": h0,
        "As": As,
        "As_prime": As_prime,
        "M": M,
        "Rb": Rb,
        "Rs": Rs,
        "Es": Es,
    }
    for name, value in values.items():
        if not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if b <= 0:
        raise ValueError("b must be positive")
    if h0 <= 0:
        raise ValueError("h0 must be positive")
    if As < 0:
        raise ValueError("As must be non-negative")
    if As_prime < 0:
        raise ValueError("As_prime must be non-negative")
    if M < 0:
        raise ValueError("M must be non-negative")
    if Rb <= 0:
        raise ValueError("Rb must be positive")
    if Rs <= 0:
        raise ValueError("Rs must be positive")
    if Es <= 0:
        raise ValueError("Es must be positive")


def _compression_zone_height(*, Rs: float, As: float, Rb: float, b: float) -> float:
    return Rs * As / (Rb * b)


def _utilization(*, M: float, Mult: float) -> float:
    if Mult <= 0:
        return 0.0 if M == 0 else inf
    return M / Mult
