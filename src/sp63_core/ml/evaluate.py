"""Metrics for the experimental baseline ML sandbox."""

from collections.abc import Sequence

from sp63_core.dataset import DatasetCase
from sp63_core.ml.baseline import BaselineModelBundle, predict_baseline_targets
from sp63_core.ml.proposal import proposal_from_prediction
from sp63_core.ml.safety import check_ml_proposal_safety


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


def evaluate_ml_safety(
    model_bundle: BaselineModelBundle,
    cases: Sequence[DatasetCase],
) -> dict[str, float]:
    """Evaluate deterministic safety outcomes for baseline ML proposals."""
    if not cases:
        raise ValueError("cases must not be empty")

    predictions = predict_baseline_targets(model_bundle, cases)
    total = len(predictions)
    accepted = 0
    bending_fail = 0
    shear_fail = 0
    layout_fail = 0
    constructive_fail = 0
    for prediction, case in zip(predictions, cases, strict=True):
        try:
            proposal, _ = proposal_from_prediction(prediction)
            safety = check_ml_proposal_safety(proposal, case)
        except ValueError:
            bending_fail += 1
            shear_fail += 1
            layout_fail += 1
            constructive_fail += 1
            continue

        if safety["accepted_by_deterministic_core"]:
            accepted += 1
        if safety["bending_status"] != "pass":
            bending_fail += 1
        if safety["shear_status"] != "pass":
            shear_fail += 1
        if not safety["layout_feasible"]:
            layout_fail += 1
        if (
            safety["longitudinal_constructive_status"] != "pass"
            or safety["transverse_constructive_status"] not in ("pass", "warning")
        ):
            constructive_fail += 1

    unsafe = total - accepted
    return {
        "total_predictions": float(total),
        "deterministic_accept_rate": accepted / total,
        "unsafe_prediction_rate": unsafe / total,
        "bending_fail_rate": bending_fail / total,
        "shear_fail_rate": shear_fail / total,
        "layout_fail_rate": layout_fail / total,
        "constructive_fail_rate": constructive_fail / total,
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
