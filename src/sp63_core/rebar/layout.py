"""Draft longitudinal reinforcement layout checks."""

from dataclasses import dataclass, field

from sp63_core.materials.rebar import area_by_diameter
from sp63_core.sections.rectangular import RectangularSection


@dataclass(frozen=True)
class RebarLayout:
    """Single-layer longitudinal reinforcement layout result."""

    bar_count: int
    diameter: float
    area: float
    scheme: str
    clear_width: float
    required_width: float
    layout_feasible: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    requires_engineer_review: bool = True


def check_single_layer_layout(
    section: RectangularSection,
    bar_count: int,
    diameter: float,
    min_clear_spacing: float = 25.0,
) -> RebarLayout:
    """Check whether bars fit into one draft reinforcement layer."""
    section.validate_geometry()
    if bar_count <= 0:
        raise ValueError("bar_count must be positive")
    if diameter <= 0:
        raise ValueError("diameter must be positive")
    if min_clear_spacing < 0:
        raise ValueError("min_clear_spacing must be non-negative")

    area = bar_count * area_by_diameter(diameter)
    scheme = f"{bar_count}D{diameter:g}"
    clear_width = section.b - 2.0 * (section.cover + section.stirrup_diameter)
    if clear_width <= 0:
        raise ValueError("clear_width must be positive")
    required_width = bar_count * diameter + (bar_count - 1) * min_clear_spacing
    layout_feasible = required_width <= clear_width
    warnings = () if layout_feasible else ("single-layer layout is not feasible",)

    return RebarLayout(
        bar_count=bar_count,
        diameter=diameter,
        area=area,
        scheme=scheme,
        clear_width=clear_width,
        required_width=required_width,
        layout_feasible=layout_feasible,
        warnings=warnings,
        requires_engineer_review=True,
    )
