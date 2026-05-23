"""Quality gates for the experimental ML sandbox."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class MLQualityGateResult:
    """Result of an advisory-only ML sandbox quality gate."""

    status: str
    warnings: tuple[str, ...]
    thresholds: dict[str, float]
    metrics: dict[str, float]
    safety_metrics: dict[str, float]
    requires_engineer_review: bool = True


def evaluate_ml_quality_gate(
    metrics: Mapping[str, float],
    safety_metrics: Mapping[str, float],
    *,
    max_unsafe_prediction_rate: float = 0.0,
    min_deterministic_accept_rate: float = 0.95,
    max_As_MAPE: float = 15.0,
) -> MLQualityGateResult:
    """Evaluate sandbox ML quality without granting calculation authority."""
    thresholds = {
        "max_unsafe_prediction_rate": max_unsafe_prediction_rate,
        "min_deterministic_accept_rate": min_deterministic_accept_rate,
        "max_As_MAPE": max_As_MAPE,
    }
    warnings: list[str] = []
    required_values = {
        "As_MAPE": metrics.get("As_MAPE"),
        "deterministic_accept_rate": safety_metrics.get("deterministic_accept_rate"),
        "unsafe_prediction_rate": safety_metrics.get("unsafe_prediction_rate"),
    }
    if any(value is None for value in required_values.values()):
        warnings.append("required ML quality metric is missing")
        status = "fail"
    else:
        status = "pass"
        if required_values["unsafe_prediction_rate"] > max_unsafe_prediction_rate:
            warnings.append("unsafe_prediction_rate exceeds threshold")
            status = "warning"
        if required_values["deterministic_accept_rate"] < min_deterministic_accept_rate:
            warnings.append("deterministic_accept_rate is below threshold")
            status = "warning"
        if required_values["As_MAPE"] > max_As_MAPE:
            warnings.append("As_MAPE exceeds threshold")
            status = "warning"

    if status == "pass":
        warnings.append("ML remains advisory-only even when quality gate passes.")

    return MLQualityGateResult(
        status=status,
        warnings=tuple(warnings),
        thresholds=thresholds,
        metrics=dict(metrics),
        safety_metrics=dict(safety_metrics),
    )
