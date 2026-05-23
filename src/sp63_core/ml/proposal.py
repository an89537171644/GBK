"""ML reinforcement proposal reconstruction helpers."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from sp63_core.materials import LONGITUDINAL_DIAMETERS, STIRRUP_DIAMETERS
from sp63_core.rebar.transverse import DEFAULT_STIRRUP_LEGS, DEFAULT_STIRRUP_SPACINGS


@dataclass(frozen=True)
class MLReinforcementProposal:
    """Discrete reinforcement proposal reconstructed from baseline ML output."""

    main_bar_count: int
    main_bar_diameter: int
    stirrup_diameter: int
    stirrup_legs: int
    stirrup_spacing: int
    source: str = "baseline_ml"
    requires_deterministic_check: bool = True


def proposal_from_prediction(
    prediction: Mapping[str, Any],
) -> tuple[MLReinforcementProposal, tuple[str, ...]]:
    """Snap raw ML outputs to supported MVP reinforcement catalogs."""
    warnings: list[str] = []
    main_bar_count = _positive_int(prediction, "main_bar_count")
    main_bar_diameter = _snap_catalog_value(
        _positive_int(prediction, "main_bar_diameter"),
        LONGITUDINAL_DIAMETERS,
        "main_bar_diameter",
        warnings,
    )
    stirrup_diameter = _snap_catalog_value(
        _positive_int(prediction, "stirrup_diameter"),
        STIRRUP_DIAMETERS,
        "stirrup_diameter",
        warnings,
    )
    stirrup_legs = _snap_catalog_value(
        _positive_int(prediction, "stirrup_legs"),
        DEFAULT_STIRRUP_LEGS,
        "stirrup_legs",
        warnings,
    )
    stirrup_spacing = _snap_catalog_value(
        _positive_int(prediction, "stirrup_spacing"),
        DEFAULT_STIRRUP_SPACINGS,
        "stirrup_spacing",
        warnings,
    )

    return (
        MLReinforcementProposal(
            main_bar_count=main_bar_count,
            main_bar_diameter=main_bar_diameter,
            stirrup_diameter=stirrup_diameter,
            stirrup_legs=stirrup_legs,
            stirrup_spacing=stirrup_spacing,
        ),
        tuple(warnings),
    )


def _positive_int(prediction: Mapping[str, Any], key: str) -> int:
    if key not in prediction:
        raise ValueError(f"prediction is missing required field {key!r}")
    value = int(round(float(prediction[key])))
    if value <= 0:
        raise ValueError(f"{key} must be positive after rounding")
    return value


def _snap_catalog_value(
    value: int,
    allowed_values: Sequence[int],
    field_name: str,
    warnings: list[str],
) -> int:
    if value in allowed_values:
        return value
    snapped = min(allowed_values, key=lambda candidate: abs(candidate - value))
    warnings.append(f"{field_name}={value} snapped to supported value {snapped}")
    return snapped
