from sp63_core.ml import evaluate_ml_quality_gate


def test_quality_gate_passes_for_good_metrics():
    result = evaluate_ml_quality_gate(
        metrics={"As_MAPE": 5.0},
        safety_metrics={
            "unsafe_prediction_rate": 0.0,
            "deterministic_accept_rate": 1.0,
        },
    )

    assert result.status == "pass"


def test_quality_gate_warns_for_unsafe_predictions():
    result = evaluate_ml_quality_gate(
        metrics={"As_MAPE": 5.0},
        safety_metrics={
            "unsafe_prediction_rate": 0.1,
            "deterministic_accept_rate": 1.0,
        },
    )

    assert result.status == "warning"
    assert "unsafe_prediction_rate exceeds threshold" in result.warnings


def test_quality_gate_warns_for_low_accept_rate():
    result = evaluate_ml_quality_gate(
        metrics={"As_MAPE": 5.0},
        safety_metrics={
            "unsafe_prediction_rate": 0.0,
            "deterministic_accept_rate": 0.5,
        },
    )

    assert result.status == "warning"
    assert "deterministic_accept_rate is below threshold" in result.warnings


def test_quality_gate_warns_for_high_As_MAPE():
    result = evaluate_ml_quality_gate(
        metrics={"As_MAPE": 30.0},
        safety_metrics={
            "unsafe_prediction_rate": 0.0,
            "deterministic_accept_rate": 1.0,
        },
    )

    assert result.status == "warning"
    assert "As_MAPE exceeds threshold" in result.warnings


def test_quality_gate_fails_when_required_metrics_missing():
    result = evaluate_ml_quality_gate(
        metrics={},
        safety_metrics={
            "unsafe_prediction_rate": 0.0,
            "deterministic_accept_rate": 1.0,
        },
    )

    assert result.status == "fail"
    assert "required ML quality metric is missing" in result.warnings
