"""Draft serviceability checks for normal crack formation.

SP 63 reference:
    Section 8.2, normal crack formation, represented here by the issue-scoped
    draft gross-section elastic MVP formula requiring engineering review from
    docs/formulas/SP63_8_2_normal_crack_formation_rectangular.md.

Inputs:
    Rectangular section geometry ``b`` and ``h`` in mm, concrete service tensile
    resistance ``Rbtser`` in MPa = N/mm2, and service bending moment ``Mser`` in
    N*mm.

Outputs:
    ``Mcrc`` in N*mm, ``utilization = Mser / Mcrc``, crack formation status,
    warnings, and intermediate protocol values.

Applicability limits:
    Rectangular heavy-concrete beams B15-B40, bending only, no axial force, no
    prestress, no transformed section, no crack width, no deflection, and no
    nonlinear deformation model.
"""

from dataclasses import dataclass

from sp63_core.materials import Concrete
from sp63_core.sections import RectangularSection


@dataclass(frozen=True)
class CrackFormationResult:
    """Result of draft normal crack formation check for a rectangular section."""

    Mser: float
    Mcrc: float
    utilization: float
    status: str
    warnings: tuple[str, ...]
    intermediate_values: dict[str, float | str | bool]
    requires_engineer_review: bool = True


def check_normal_crack_formation_rectangular(
    section: RectangularSection,
    concrete: Concrete,
    Mser: float,
) -> CrackFormationResult:
    """Check normal crack formation using ``Mcrc = Rbtser * W``."""
    section.validate_geometry()
    if Mser < 0:
        raise ValueError("Mser must be non-negative")
    if concrete.Rbtser <= 0:
        raise ValueError("concrete.Rbtser must be positive")
    if section.b <= 0:
        raise ValueError("section width must be positive")
    if section.h <= 0:
        raise ValueError("section height must be positive")

    b = section.b
    h = section.h
    area = b * h
    inertia = b * h**3 / 12.0
    yt = h / 2.0
    section_modulus = inertia / yt
    Mcrc = concrete.Rbtser * section_modulus
    utilization = Mser / Mcrc
    status = "no_crack" if Mser <= Mcrc else "crack"

    warnings = [
        "draft gross-section crack formation check; transformed section is not implemented"
    ]
    if status == "crack":
        warnings.append(
            "normal cracks are expected; crack width check is required in next serviceability step"
        )

    return CrackFormationResult(
        Mser=Mser,
        Mcrc=Mcrc,
        utilization=utilization,
        status=status,
        warnings=tuple(warnings),
        intermediate_values={
            "b": b,
            "h": h,
            "A": area,
            "I": inertia,
            "yt": yt,
            "W": section_modulus,
            "Rbtser": concrete.Rbtser,
            "formula": "Mcrc = Rbtser * W",
            "serviceability_scope": "normal_crack_formation_only",
            "transformed_section_used": False,
        },
        requires_engineer_review=True,
    )
