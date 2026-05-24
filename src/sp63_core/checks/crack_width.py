"""Draft serviceability checks for normal crack width."""

from dataclasses import dataclass

from sp63_core.checks.cracking import (
    CrackFormationResult,
    check_normal_crack_formation_rectangular,
)
from sp63_core.materials import Concrete, Rebar
from sp63_core.sections import RectangularSection

DRAFT_CRACK_WIDTH_WARNING = (
    "draft crack width check; refined SP 63 crack spacing and tension stiffening model is not "
    "implemented"
)


@dataclass(frozen=True)
class CrackWidthResult:
    """Result of draft normal crack width check for a rectangular section."""

    Mser: float
    Mcrc: float
    acrc: float
    acrc_limit: float
    utilization: float
    sigma_s: float
    epsilon_s: float
    crack_spacing: float
    status: str
    warnings: tuple[str, ...]
    intermediate_values: dict[str, float | str | bool]
    requires_engineer_review: bool = True


def check_normal_crack_width_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    Mser: float,
    As: float,
    main_bar_diameter: float,
    *,
    acrc_limit: float = 0.3,
    crack_formation: CrackFormationResult | None = None,
) -> CrackWidthResult:
    """Check draft normal crack width using a simplified elastic cracked estimate."""
    section.validate_geometry()
    if Mser < 0:
        raise ValueError("Mser must be non-negative")
    if As <= 0:
        raise ValueError("As must be positive")
    if main_bar_diameter <= 0:
        raise ValueError("main_bar_diameter must be positive")
    if concrete.Rbtser <= 0:
        raise ValueError("concrete.Rbtser must be positive")
    if rebar.Es <= 0:
        raise ValueError("rebar.Es must be positive")
    if rebar.Rsser <= 0:
        raise ValueError("rebar.Rsser must be positive")
    if acrc_limit <= 0:
        raise ValueError("acrc_limit must be positive")

    crack_formation_result = crack_formation or check_normal_crack_formation_rectangular(
        section=section,
        concrete=concrete,
        Mser=Mser,
    )
    h0 = section.effective_depth()
    z = 0.9 * h0
    rho_eff = As / (section.b * h0)
    rho_eff_min = 0.001
    rho_eff_used = max(rho_eff, rho_eff_min)
    raw_crack_spacing = 0.5 * main_bar_diameter / rho_eff_used
    crack_spacing_min = 100.0
    crack_spacing_max = 400.0

    if crack_formation_result.status == "no_crack":
        return CrackWidthResult(
            Mser=Mser,
            Mcrc=crack_formation_result.Mcrc,
            acrc=0.0,
            acrc_limit=acrc_limit,
            utilization=0.0,
            sigma_s=0.0,
            epsilon_s=0.0,
            crack_spacing=0.0,
            status="not_required",
            warnings=(
                DRAFT_CRACK_WIDTH_WARNING,
                "normal cracks are not expected; crack width check is not required in this draft",
            ),
            intermediate_values=_intermediate_values(
                h0=h0,
                z=z,
                As=As,
                main_bar_diameter=main_bar_diameter,
                rho_eff=rho_eff,
                rho_eff_used=rho_eff_used,
                raw_crack_spacing=raw_crack_spacing,
                crack_spacing_min=crack_spacing_min,
                crack_spacing_max=crack_spacing_max,
                crack_spacing=0.0,
                sigma_s=0.0,
                Rsser=rebar.Rsser,
                Es=rebar.Es,
                epsilon_s=0.0,
                acrc_limit=acrc_limit,
                Mser=Mser,
                Mcrc=crack_formation_result.Mcrc,
            ),
            requires_engineer_review=True,
        )
    if crack_formation_result.status != "crack":
        raise ValueError("crack_formation.status must be 'no_crack' or 'crack'")

    sigma_s = Mser / (As * z)
    epsilon_s = sigma_s / rebar.Es
    crack_spacing = min(
        max(raw_crack_spacing, crack_spacing_min),
        crack_spacing_max,
    )
    acrc = epsilon_s * crack_spacing
    utilization = acrc / acrc_limit
    status = "pass" if acrc <= acrc_limit else "fail"

    warnings = [DRAFT_CRACK_WIDTH_WARNING]
    if sigma_s > rebar.Rsser:
        warnings.append("service reinforcement stress exceeds Rsser; engineer review is required")
    if status == "fail":
        warnings.append("crack width exceeds draft limit")

    return CrackWidthResult(
        Mser=Mser,
        Mcrc=crack_formation_result.Mcrc,
        acrc=acrc,
        acrc_limit=acrc_limit,
        utilization=utilization,
        sigma_s=sigma_s,
        epsilon_s=epsilon_s,
        crack_spacing=crack_spacing,
        status=status,
        warnings=tuple(warnings),
        intermediate_values=_intermediate_values(
            h0=h0,
            z=z,
            As=As,
            main_bar_diameter=main_bar_diameter,
            rho_eff=rho_eff,
            rho_eff_used=rho_eff_used,
            raw_crack_spacing=raw_crack_spacing,
            crack_spacing_min=crack_spacing_min,
            crack_spacing_max=crack_spacing_max,
            crack_spacing=crack_spacing,
            sigma_s=sigma_s,
            Rsser=rebar.Rsser,
            Es=rebar.Es,
            epsilon_s=epsilon_s,
            acrc_limit=acrc_limit,
            Mser=Mser,
            Mcrc=crack_formation_result.Mcrc,
        ),
        requires_engineer_review=True,
    )


def _intermediate_values(
    *,
    h0: float,
    z: float,
    As: float,
    main_bar_diameter: float,
    rho_eff: float,
    rho_eff_used: float,
    raw_crack_spacing: float,
    crack_spacing_min: float,
    crack_spacing_max: float,
    crack_spacing: float,
    sigma_s: float,
    Rsser: float,
    Es: float,
    epsilon_s: float,
    acrc_limit: float,
    Mser: float,
    Mcrc: float,
) -> dict[str, float | str | bool]:
    return {
        "h0": h0,
        "z": z,
        "As": As,
        "main_bar_diameter": main_bar_diameter,
        "rho_eff": rho_eff,
        "rho_eff_used": rho_eff_used,
        "raw_crack_spacing": raw_crack_spacing,
        "crack_spacing_min": crack_spacing_min,
        "crack_spacing_max": crack_spacing_max,
        "crack_spacing": crack_spacing,
        "sigma_s": sigma_s,
        "Rsser": Rsser,
        "Es": Es,
        "epsilon_s": epsilon_s,
        "acrc_limit": acrc_limit,
        "Mser": Mser,
        "Mcrc": Mcrc,
        "formula": "acrc = sigma_s / Es * crack_spacing",
        "crack_spacing_model": "draft bounded spacing",
        "tension_stiffening_model": "not_implemented",
        "transformed_section_used": False,
        "serviceability_scope": "normal_crack_width_only",
    }
