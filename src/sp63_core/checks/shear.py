"""Shear check for the SP 63 MVP.

Formula source: docs/formulas/SP63_8_1_33_shear.md.

Units:
- forces: N
- dimensions: mm
- stresses: MPa = N/mm2
- transverse reinforcement area: mm2
"""

from dataclasses import dataclass, field
from math import inf
from typing import Literal

from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import Rebar
from sp63_core.sections.rectangular import RectangularSection

ShearStatus = Literal["pass", "fail"]
PHI_B1 = 0.3
PHI_B2 = 1.5
PHI_SW = 0.75
SOURCE_CLAUSE = "SP 63.13330.2018 8.1.31-8.1.33"


@dataclass(frozen=True)
class ShearResult:
    """Result of rectangular shear check."""

    Q_strip: float
    qsw: float
    Qb: float
    Qsw: float
    Qult: float
    utilization: float
    status: ShearStatus
    warnings: tuple[str, ...] = field(default_factory=tuple)
    intermediate_values: dict[str, float | str | bool] = field(default_factory=dict)
    source_clause: str = SOURCE_CLAUSE
    requires_engineer_review: bool = True


def check_shear_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    stirrup_rebar: Rebar,
    Q: float,
    Asw: float,
    sw: float,
    *,
    c_points: int = 101,
) -> ShearResult:
    """Check rectangular shear capacity using the draft MVP formula card.

    The formula and its applicability still require engineering review.
    """
    section.validate_geometry()
    b = section.b
    h0 = section.effective_depth()
    Rb = concrete.Rb
    Rbt = concrete.Rbt
    Rsw = stirrup_rebar.Rsw

    _validate_inputs(
        b=b,
        h0=h0,
        Rb=Rb,
        Rbt=Rbt,
        Rsw=Rsw,
        Q=Q,
        Asw=Asw,
        sw=sw,
        c_points=c_points,
    )

    Q_strip = PHI_B1 * Rb * b * h0
    qsw = Rsw * Asw / sw
    sw_max_by_shear_rule = Rbt * b * h0**2 / Q if Q > 0 else inf
    transverse_reinforcement_countable = Asw > 0 and sw <= sw_max_by_shear_rule
    qsw_min_rule = 0.25 * Rbt * b
    if Asw > 0:
        qsw_rule_status = "pass" if qsw >= qsw_min_rule else "warning"
    else:
        qsw_rule_status = "not_applicable"
    best = _find_minimum_qult(b=b, h0=h0, Rbt=Rbt, qsw=qsw, c_points=c_points)
    Qult = best["Qult"]
    utilization = _utilization(Q=Q, Qult=Qult)

    warnings: list[str] = []
    if Q_strip < Q:
        warnings.append("shear force exceeds concrete strip capacity")
    if Qult < Q:
        warnings.append("shear force exceeds inclined section capacity")
    if Asw > 0 and sw > sw_max_by_shear_rule:
        warnings.append(
            "stirrup spacing exceeds shear rule maximum for counting transverse reinforcement"
        )
    if Asw > 0 and qsw < qsw_min_rule:
        warnings.append("qsw is below draft minimum rule for counting transverse reinforcement")

    status: ShearStatus = "pass" if Q_strip >= Q and Qult >= Q else "fail"
    intermediate_values: dict[str, float | str | bool] = {
        "b": b,
        "h0": h0,
        "Rb": Rb,
        "Rbt": Rbt,
        "Rsw": Rsw,
        "Q": Q,
        "Asw": Asw,
        "sw": sw,
        "sw_max_by_shear_rule": sw_max_by_shear_rule,
        "transverse_reinforcement_countable": transverse_reinforcement_countable,
        "qsw_min_rule": qsw_min_rule,
        "qsw_rule_status": qsw_rule_status,
        "phi_b1": PHI_B1,
        "phi_b2": PHI_B2,
        "phi_sw": PHI_SW,
        "Q_strip": Q_strip,
        "qsw": qsw,
        "C": best["C"],
        "C_min": h0,
        "C_max": 2.0 * h0,
        "Qb_raw": best["Qb_raw"],
        "Qb_min": best["Qb_min"],
        "Qb_max": best["Qb_max"],
        "Qb": best["Qb"],
        "Qsw": best["Qsw"],
        "Qult": Qult,
        "utilization": utilization,
        "source_clause": SOURCE_CLAUSE,
        "requires_engineer_review": True,
    }

    return ShearResult(
        Q_strip=Q_strip,
        qsw=qsw,
        Qb=best["Qb"],
        Qsw=best["Qsw"],
        Qult=Qult,
        utilization=utilization,
        status=status,
        warnings=tuple(warnings),
        intermediate_values=intermediate_values,
    )


def _validate_inputs(
    *,
    b: float,
    h0: float,
    Rb: float,
    Rbt: float,
    Rsw: float,
    Q: float,
    Asw: float,
    sw: float,
    c_points: int,
) -> None:
    if b <= 0:
        raise ValueError("b must be positive")
    if h0 <= 0:
        raise ValueError("h0 must be positive")
    if Rb <= 0:
        raise ValueError("Rb must be positive")
    if Rbt <= 0:
        raise ValueError("Rbt must be positive")
    if Rsw <= 0:
        raise ValueError("Rsw must be positive")
    if Q < 0:
        raise ValueError("Q must be non-negative")
    if Asw < 0:
        raise ValueError("Asw must be non-negative")
    if sw <= 0:
        raise ValueError("sw must be positive")
    if c_points < 2:
        raise ValueError("c_points must be at least 2")


def _find_minimum_qult(
    *, b: float, h0: float, Rbt: float, qsw: float, c_points: int
) -> dict[str, float]:
    c_min = h0
    c_max = 2.0 * h0
    step = (c_max - c_min) / (c_points - 1)
    best: dict[str, float] | None = None

    for index in range(c_points):
        C = c_min + step * index
        Qb_raw = PHI_B2 * Rbt * b * h0**2 / C
        Qb_min = 0.5 * Rbt * b * h0
        Qb_max = 2.5 * Rbt * b * h0
        Qb = min(max(Qb_raw, Qb_min), Qb_max)
        Qsw = PHI_SW * qsw * C
        Qult = Qb + Qsw
        current = {
            "C": C,
            "Qb_raw": Qb_raw,
            "Qb_min": Qb_min,
            "Qb_max": Qb_max,
            "Qb": Qb,
            "Qsw": Qsw,
            "Qult": Qult,
        }
        if best is None or Qult < best["Qult"]:
            best = current

    if best is None:
        raise RuntimeError("C range search produced no values")
    return best


def _utilization(*, Q: float, Qult: float) -> float:
    if Qult <= 0:
        return 0.0 if Q == 0 else inf
    return Q / Qult
