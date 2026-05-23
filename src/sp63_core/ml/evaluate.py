"""Metrics for the experimental baseline ML sandbox."""

from collections.abc import Sequence

from sp63_core.dataset import DatasetCase
from sp63_core.ml.baseline import BaselineModelBundle, predict_baseline_targets


def evaluate_baseline_models(
    model_bundle: BaselineModelBundle,
    test_cases: Sequence[DatasetCase],
) -> dict[str, float]:
    """Evaluate baseline predictions against deterministic dataset targets."""
    if not test_cases:
        raise ValueError("test_cases must not be empty")

    predictions = predict_baseline_targets(model_bundle, test_cases)
    return {
        "As_MAE": _mean_absolute_error(
            [case.As_provided for case in test_cases],
            [prediction["As_provided"] for prediction in predictions],
        ),
        "As_MAPE": _mean_absolute_percentage_error(
            [case.As_provided for case in test_cases],
            [prediction["As_provided"] for prediction in predictions],
        ),
        "bending_utilization_MAE": _mean_absolute_error(
            [case.bending_utilization for case in test_cases],
            [prediction["bending_utilization"] for prediction in predictions],
        ),
        "shear_utilization_MAE": _mean_absolute_error(
            [case.shear_utilization for case in test_cases],
            [prediction["shear_utilization"] for prediction in predictions],
        ),
        "main_bar_diameter_accuracy": _accuracy(
            [case.main_bar_diameter for case in test_cases],
            [prediction["main_bar_diameter"] for prediction in predictions],
        ),
        "main_bar_count_accuracy": _accuracy(
            [case.main_bar_count for case in test_cases],
            [prediction["main_bar_count"] for prediction in predictions],
        ),
        "stirrup_diameter_accuracy": _accuracy(
            [case.stirrup_diameter for case in test_cases],
            [prediction["stirrup_diameter"] for prediction in predictions],
        ),
        "stirrup_spacing_accuracy": _accuracy(
            [case.stirrup_spacing for case in test_cases],
            [prediction["stirrup_spacing"] for prediction in predictions],
        ),
    }


def _mean_absolute_error(
    actual: Sequence[float],
    predicted: Sequence[float | int],
) -> float:
    total_error = sum(
        abs(float(a) - float(p))
        for a, p in zip(actual, predicted, strict=True)
    )
    return total_error / len(actual)


def _mean_absolute_percentage_error(
    actual: Sequence[float],
    predicted: Sequence[float | int],
) -> float:
    values = [
        abs(float(a) - float(p)) / abs(float(a)) * 100.0
        for a, p in zip(actual, predicted, strict=True)
        if float(a) != 0.0
    ]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _accuracy(
    actual: Sequence[int],
    predicted: Sequence[float | int],
) -> float:
    return sum(1 for a, p in zip(actual, predicted, strict=True) if int(a) == int(p)) / len(actual)
