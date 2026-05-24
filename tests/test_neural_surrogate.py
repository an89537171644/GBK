"""Tests for the K29 advisory-only neural surrogate smoke report."""

import json

from sp63_core.cli import main
from sp63_core.ml import build_neural_surrogate_report


def test_build_neural_surrogate_report_is_advisory_only():
    report = build_neural_surrogate_report(diagnostic_limit=100)

    assert report.neural_network_used is True
    assert report.ml_is_advisory_only is True
    assert report.deterministic_checks_required is True
    assert report.requires_engineer_review is True
    assert report.classification_target == "overall_status"
    assert report.classification_metrics["model"] == "MLPClassifier"
    assert report.classification_metrics["accuracy"] >= 0.0
    assert report.classification_metrics["macro_f1"] >= 0.0
    assert "longitudinal_as_mm2" in report.regression_metrics
    assert "bending_utilization" in report.regression_metrics
    assert any("must not be used as a design checker" in warning for warning in report.warnings)
    assert any("deterministic SP63 verification" in warning for warning in report.warnings)


def test_cli_neural_surrogate_json_output(capsys):
    exit_code = main(["neural-surrogate", "--diagnostic-limit", "100", "--json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "neural-surrogate"
    assert data["neural_network_used"] is True
    assert data["ml_is_advisory_only"] is True
    assert data["deterministic_checks_required"] is True
    assert data["requires_engineer_review"] is True
    assert data["classification_metrics"]["target"] == "overall_status"
    assert "confusion_matrix" in data["classification_metrics"]
    assert "longitudinal_as_mm2" in data["regression_metrics"]
    assert any("not be used as a design checker" in warning for warning in data["warnings"])
