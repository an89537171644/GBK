"""Rectangular bending section check for the SP 63 MVP.

Formula source: docs/formulas/SP63_8_1_9_bending_rectangular.md.

Units:
- forces: N
- moments: N*mm
- dimensions: mm
- stresses: MPa = N/mm2
- reinforcement areas: mm2

Scope:
- rectangular bending element;
- heavy concrete B15-B40 in the MVP material catalog;
- no automatic substitution of x = xi_R * h0.
"""

from dataclasses import dataclass, field
from math import inf
from typing import Literal

from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import LoadDuration, Rebar
from sp63_core.sections.rectangular import RectangularSection

BendingStatus = Literal["pass", "fail", "review_or_fail"]
EB2 = 0.0035
SOURCE_CLAUSE = "SP 63.13330.2018 8.1.8-8.1.9"


@dataclass(frozen=True)
class BendingResult:
    """Result of rectangular bending section check."""

    x: float
    xi: float
    xi_R: float
    Mult: float
    utilization: float
    status: BendingStatus
    warnings: tuple[str, ...] = field(default_factory=tuple)
    intermediate_values: dict[str, float | str | bool] = field(default_factory=dict)
    source_clause: str = SOURCE_CLAUSE
    requires_engineer_review: bool = True


def check_bending_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    As: float,
    M: float,
    As_prime: float = 0.0,
    Rsc_override: float | None = None,
    load_duration: LoadDuration = "short",
) -> BendingResult:
    """Check rectangular bending capacity using the approved MVP formula card."""
    section.validate_geometry()
    b = section.b
    h0 = section.effective_depth()
    a_prime = section.compression_rebar_depth()
    Rb = concrete.Rb
    Rs = rebar.Rs
    Rsc = Rsc_override if Rsc_override is not None else rebar.get_Rsc(load_duration)
    Es = rebar.Es

    _validate_inputs(
        b=b,
        h0=h0,
        As=As,
        As_prime=As_prime,
        M=M,
        Rb=Rb,
        Rs=Rs,
        Rsc=Rsc,
        Es=Es,
    )

    xi_R = 0.8 / (1.0 + (Rs / Es) / EB2)
    x = _compression_zone_height(Rs=Rs, As=As, Rsc=Rsc, As_prime=As_prime, Rb=Rb, b=b)
    xi = x / h0
    x_limit = xi_R * h0

    warnings: list[str] = []
    if x <= 0:
        Mult = 0.0
        utilization = _utilization(M=M, Mult=Mult)
        warnings.append("non-positive compression zone height")
        status: BendingStatus = "fail"
    else:
        Mult = Rb * b * x * (h0 - 0.5 * x) + Rsc * As_prime * (h0 - a_prime)
        utilization = _utilization(M=M, Mult=Mult)
        if x > x_limit:
            warnings.append(
                "compression zone height exceeds xi_R * h0; engineering review required"
            )
            status = "review_or_fail"
        elif Mult >= M:
            status = "pass"
        else:
            status = "fail"

    intermediate_values: dict[str, float | str | bool] = {
        "b": b,
        "h0": h0,
        "a_prime": a_prime,
        "Rb": Rb,
        "Rs": Rs,
        "Rsc": Rsc,
        "Es": Es,
        "load_duration": load_duration,
        "As": As,
        "As_prime": As_prime,
        "M": M,
        "eb2": EB2,
        "x": x,
        "xi": xi,
        "xi_R": xi_R,
        "x_limit": x_limit,
        "Mult": Mult,
        "utilization": utilization,
        "source_clause": SOURCE_CLAUSE,
        "requires_engineer_review": True,
    }

    return BendingResult(
        x=x,
        xi=xi,
        xi_R=xi_R,
        Mult=Mult,
        utilization=utilization,
        status=status,
        warnings=tuple(warnings),
        intermediate_values=intermediate_values,
    )


def _validate_inputs(
    *,
    b: float,
    h0: float,
    As: float,
    As_prime: float,
    M: float,
    Rb: float,
    Rs: float,
    Rsc: float,
    Es: float,
) -> None:
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
    if Rsc <= 0:
        raise ValueError("Rsc must be positive")
    if Es <= 0:
        raise ValueError("Es must be positive")


def _compression_zone_height(
    *, Rs: float, As: float, Rsc: float, As_prime: float, Rb: float, b: float
) -> float:
    if As_prime == 0:
        return Rs * As / (Rb * b)
    return (Rs * As - Rsc * As_prime) / (Rb * b)


def _utilization(*, M: float, Mult: float) -> float:
    if Mult <= 0:
        return 0.0 if M == 0 else inf
    return M / Mult
