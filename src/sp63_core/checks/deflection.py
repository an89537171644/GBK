"""Draft serviceability checks for curvature and deflection."""

from dataclasses import dataclass
from math import sqrt

from sp63_core.checks.cracking import (
    CrackFormationResult,
    check_normal_crack_formation_rectangular,
)
from sp63_core.materials import Concrete, Rebar
from sp63_core.sections import RectangularSection

DRAFT_DEFLECTION_WARNING = (
    "draft deflection check; refined SP 63 curvature, cracking, long-term effects, "
    "creep, shrinkage, and tension stiffening are not implemented"
)
SUPPORTED_LOADING_SCHEME = "simply_supported_uniform"


@dataclass(frozen=True)
class DeflectionResult:
    """Result of draft curvature and deflection check for a rectangular section."""

    Mser: float
    Mcrc: float
    span: float
    curvature: float
    deflection: float
    deflection_limit: float
    utilization: float
    I_gross: float
    I_cracked: float
    I_eff: float
    stiffness_status: str
    loading_scheme: str
    status: str
    warnings: tuple[str, ...]
    intermediate_values: dict[str, float | str | bool]
    requires_engineer_review: bool = True


def check_curvature_deflection_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    Mser: float,
    As: float,
    span: float,
    *,
    deflection_limit: float | None = None,
    deflection_limit_ratio: float = 250.0,
    loading_scheme: str = SUPPORTED_LOADING_SCHEME,
    crack_formation: CrackFormationResult | None = None,
) -> DeflectionResult:
    """Check draft short-term curvature and deflection for a rectangular beam."""
    section.validate_geometry()
    if Mser < 0:
        raise ValueError("Mser must be non-negative")
    if As <= 0:
        raise ValueError("As must be positive")
    if span <= 0:
        raise ValueError("span must be positive")
    if concrete.Eb <= 0:
        raise ValueError("concrete.Eb must be positive")
    if rebar.Es <= 0:
        raise ValueError("rebar.Es must be positive")
    if deflection_limit_ratio <= 0:
        raise ValueError("deflection_limit_ratio must be positive")
    if deflection_limit is not None and deflection_limit <= 0:
        raise ValueError("deflection_limit must be positive")
    if loading_scheme != SUPPORTED_LOADING_SCHEME:
        raise ValueError("loading_scheme must be 'simply_supported_uniform'")

    crack_formation_result = crack_formation or check_normal_crack_formation_rectangular(
        section=section,
        concrete=concrete,
        Mser=Mser,
    )
    if crack_formation_result.status not in ("no_crack", "crack"):
        raise ValueError("crack_formation.status must be 'no_crack' or 'crack'")

    h0 = section.effective_depth()
    b = section.b
    h = section.h
    I_gross = b * h**3 / 12.0
    n = rebar.Es / concrete.Eb
    neutral_axis_x = _cracked_neutral_axis_depth(b=b, h0=h0, As=As, n=n)
    I_cracked = b * neutral_axis_x**3 / 3.0 + n * As * (h0 - neutral_axis_x) ** 2

    warnings = [DRAFT_DEFLECTION_WARNING]
    if crack_formation_result.status == "no_crack":
        I_eff = I_gross
        stiffness_status = "gross_uncracked"
    else:
        I_eff = I_cracked
        stiffness_status = "draft_cracked_transformed"
        warnings.append("cracked transformed stiffness is simplified and requires engineer review")

    curvature = 0.0 if Mser == 0 else Mser / (concrete.Eb * I_eff)
    deflection = 5.0 / 48.0 * curvature * span**2
    limit = deflection_limit if deflection_limit is not None else span / deflection_limit_ratio
    utilization = deflection / limit
    status = "pass" if deflection <= limit else "fail"
    if status == "fail":
        warnings.append("deflection exceeds draft limit")

    return DeflectionResult(
        Mser=Mser,
        Mcrc=crack_formation_result.Mcrc,
        span=span,
        curvature=curvature,
        deflection=deflection,
        deflection_limit=limit,
        utilization=utilization,
        I_gross=I_gross,
        I_cracked=I_cracked,
        I_eff=I_eff,
        stiffness_status=stiffness_status,
        loading_scheme=loading_scheme,
        status=status,
        warnings=tuple(warnings),
        intermediate_values={
            "h0": h0,
            "b": b,
            "h": h,
            "As": As,
            "span": span,
            "Mser": Mser,
            "Mcrc": crack_formation_result.Mcrc,
            "Eb": concrete.Eb,
            "Es": rebar.Es,
            "n": n,
            "I_gross": I_gross,
            "I_cracked": I_cracked,
            "I_eff": I_eff,
            "neutral_axis_x": neutral_axis_x,
            "curvature": curvature,
            "deflection": deflection,
            "deflection_limit": limit,
            "deflection_limit_ratio": deflection_limit_ratio,
            "loading_scheme": loading_scheme,
            "stiffness_status": stiffness_status,
            "formula_curvature": "curvature = Mser / (Eb * I_eff)",
            "formula_deflection": "f = 5/48 * curvature * span^2 for simply_supported_uniform",
            "long_term_effects": "not_implemented",
            "tension_stiffening_model": "not_implemented",
            "nonlinear_deformation_model": "not_implemented",
            "serviceability_scope": "draft_curvature_and_deflection_only",
        },
        requires_engineer_review=True,
    )


def _cracked_neutral_axis_depth(*, b: float, h0: float, As: float, n: float) -> float:
    a = 0.5 * b
    coefficient_b = n * As
    coefficient_c = -n * As * h0
    discriminant = coefficient_b**2 - 4.0 * a * coefficient_c
    return (-coefficient_b + sqrt(discriminant)) / (2.0 * a)
