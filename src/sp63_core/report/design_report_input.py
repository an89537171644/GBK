"""Input helpers for rectangular design report generation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sp63_core.design import RectangularDesignInput

REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS = (
    "b",
    "h",
    "cover",
    "stirrup_diameter_for_geometry",
    "concrete_class",
    "longitudinal_rebar_class",
    "stirrup_rebar_class",
    "M",
    "Q",
    "local_axes_id",
    "moment_axis",
    "tension_face",
    "load_duration",
)

OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS = (
    "Mser",
    "check_cracks",
    "check_crack_width",
    "check_deflection",
    "span",
    "acrc_limit",
    "deflection_limit",
    "deflection_limit_ratio",
)

ALLOWED_RECTANGULAR_DESIGN_INPUT_FIELDS = (
    *REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS,
    *OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS,
)


def load_rectangular_design_input_from_json(path: str | Path) -> RectangularDesignInput:
    """Load rectangular design input from a JSON file."""
    json_path = Path(path)
    with json_path.open(encoding="utf-8") as input_file:
        data = json.load(input_file)
    if not isinstance(data, dict):
        raise ValueError("design report input JSON must contain an object")
    return rectangular_design_input_from_mapping(data)


def rectangular_design_input_from_mapping(data: Mapping[str, Any]) -> RectangularDesignInput:
    """Build rectangular design input from a mapping with explicit field checks."""
    from sp63_core.design import RectangularDesignInput

    missing_fields = tuple(
        field for field in REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS if field not in data
    )
    if missing_fields:
        raise ValueError(
            "missing required design report input fields: " + ", ".join(missing_fields)
        )

    unknown_fields = tuple(
        sorted(field for field in data if field not in ALLOWED_RECTANGULAR_DESIGN_INPUT_FIELDS)
    )
    if unknown_fields:
        raise ValueError("unknown design report input fields: " + ", ".join(unknown_fields))

    input_values = {field: data[field] for field in REQUIRED_RECTANGULAR_DESIGN_INPUT_FIELDS}
    input_values.update(
        {
            field: data[field]
            for field in OPTIONAL_RECTANGULAR_DESIGN_INPUT_FIELDS
            if field in data
        }
    )
    design_input = RectangularDesignInput(**input_values)
    design_input.bending_orientation()
    if design_input.load_duration not in ("short", "long"):
        raise ValueError("load_duration must be 'short' or 'long'")
    return design_input
