"""Draft deterministic safety wrapper for ML predictions."""

from collections.abc import Mapping
from typing import Any

from sp63_core.dataset import DatasetCase
from sp63_core.design import RectangularDesignInput, design_rectangular_element

ADVISORY_WARNING = (
    "draft ML safety gate: baseline ML is advisory only; deterministic SP63 checks "
    "remain mandatory"
)


def check_ml_prediction_safety(
    prediction: Mapping[str, Any],
    original_case: DatasetCase,
) -> dict[str, Any]:
    """Check an ML proposal against the deterministic design workflow.

    K12 intentionally does not reconstruct an exact ML reinforcement scheme. The
    safety gate reruns the deterministic core for the original case and reports
    whether that deterministic design passes.
    """
    design_input = RectangularDesignInput(
        b=original_case.b,
        h=original_case.h,
        cover=_infer_cover(original_case),
        stirrup_diameter_for_geometry=original_case.geometry_stirrup_diameter,
        concrete_class=original_case.concrete_class,
        longitudinal_rebar_class=original_case.rebar_class,
        stirrup_rebar_class=original_case.stirrup_class,
        M=original_case.M,
        Q=original_case.Q,
        load_duration=original_case.load_duration,
    )
    deterministic_result = design_rectangular_element(design_input)
    return {
        "deterministic_status": deterministic_result.status,
        "ml_is_advisory": True,
        "accepted_by_deterministic_core": deterministic_result.status == "pass",
        "warnings": (
            ADVISORY_WARNING,
            *deterministic_result.warnings,
        ),
        "prediction_keys": tuple(sorted(prediction)),
    }


def _infer_cover(case: DatasetCase) -> float:
    cover = (
        case.h
        - case.h0
        - case.geometry_stirrup_diameter
        - case.main_bar_diameter / 2.0
    )
    if cover <= 0:
        raise ValueError("cannot infer positive cover from dataset case")
    return cover
