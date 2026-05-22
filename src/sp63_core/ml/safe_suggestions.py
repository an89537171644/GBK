"""Safe reinforcement suggestions from ML predictions."""

from dataclasses import dataclass

from sp63_core.materials.concrete import Concrete
from sp63_core.materials.rebar import Rebar
from sp63_core.rebar import LongitudinalRebarOption, select_longitudinal_rebar
from sp63_core.sections.rectangular import RectangularSection


@dataclass(frozen=True)
class SafeLongitudinalSuggestion:
    """Deterministically checked longitudinal reinforcement suggestions."""

    predicted_As: float
    selected_options: tuple[LongitudinalRebarOption, ...]
    unsafe_accept_rate: float = 0.0
    requires_deterministic_check: bool = True


def suggest_checked_longitudinal_options(
    *,
    predicted_As: float,
    section: RectangularSection,
    concrete: Concrete,
    rebar: Rebar,
    M: float,
    max_results: int = 5,
) -> SafeLongitudinalSuggestion:
    """Return passing deterministic options sorted by closeness to predicted As."""
    if max_results <= 0:
        raise ValueError("max_results must be positive")

    options = select_longitudinal_rebar(
        section=section,
        concrete=concrete,
        rebar=rebar,
        M=M,
        max_results=max(max_results, 50),
    )
    sorted_options = sorted(
        options,
        key=lambda option: (abs(option.As - predicted_As), option.As),
    )

    return SafeLongitudinalSuggestion(
        predicted_As=predicted_As,
        selected_options=tuple(sorted_options[:max_results]),
        unsafe_accept_rate=0.0,
        requires_deterministic_check=True,
    )
