import json

from sp63_core.cli import main
from sp63_core.dataset import export_dataset_from_report_archive
from sp63_core.ml.report_neural_prediction import NeuralAdvisoryPredictionResult
from sp63_core.ml.report_neural_safety_audit import (
    build_neural_advisory_safety_audit,
)

BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"
INPUT_JSON = "docs/reports/examples/rectangular_design_input_example.json"


def _write_batch_archive(output_dir) -> int:
    return main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    )


def _write_batch_dataset(tmp_path, *, output_format="jsonl"):
    source_dir = tmp_path / "batch_bundle"
    suffix = "csv" if output_format == "csv" else output_format
    output_path = tmp_path / f"batch_dataset.{suffix}"
    assert _write_batch_archive(source_dir) == 0
    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
        output_format=output_format,
    )
    assert result.status == "pass"
    return output_path


def test_neural_safety_audit_builds_from_jsonl(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.status in {"review_required", "fail"}
    assert result.audit_status in {"review_required", "fail"}
    assert result.predicted_status is None
    assert result.deterministic_strength_status == "outside_applicability"
    assert result.deterministic_serviceability_status == "pass"
    assert result.deterministic_overall_status == "outside_applicability"
    assert result.prediction_matches_deterministic is None
    assert isinstance(result.advisory_signal_usable, bool)
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.requires_engineer_review is True
    assert result.json_data["report_type"] == "neural_advisory_safety_audit"
    assert result.json_data["class_probabilities"] == {}
    assert result.neural_network_used is False


def test_neural_safety_audit_builds_from_csv(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        dataset_format="csv",
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.source_dataset == str(dataset_path)
    assert result.predicted_status is None
    assert result.json_data["class_probabilities"] == {}


def test_neural_safety_audit_deterministic_derived_warns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        feature_mode="deterministic_derived",
        max_iter=50,
    )

    assert result.feature_mode == "deterministic_derived"
    assert any(
        "deterministic-derived features may leak design decisions" in warning
        for warning in result.warnings
    )


def test_neural_safety_audit_markdown_contains_required_sections(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert "Neural Advisory Safety Audit" in result.markdown
    assert "Deterministic SP63 verification" in result.markdown
    assert "This audit is advisory-only" in result.markdown


def test_neural_safety_audit_mismatch_fails(monkeypatch, tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    def fake_prediction(**_kwargs):
        return NeuralAdvisoryPredictionResult(
            status="review_required",
            source_dataset=str(dataset_path),
            input_json_path=INPUT_JSON,
            target="overall_status",
            feature_mode="input_only",
            predicted_status="fail",
            prediction_confidence=0.99,
            class_probabilities={"fail": 0.99, "pass": 0.01},
            deterministic_strength_status="pass",
            deterministic_serviceability_status="pass",
            deterministic_overall_status="pass",
            prediction_matches_deterministic=False,
            neural_network_used=True,
            warnings=(
                "neural advisory prediction differs from deterministic SP63 result",
            ),
        )

    monkeypatch.setattr(
        "sp63_core.ml.report_neural_safety_audit.build_neural_advisory_prediction",
        fake_prediction,
    )

    result = build_neural_advisory_safety_audit(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
    )

    assert result.audit_status == "fail"
    assert result.status == "fail"
    assert result.advisory_signal_usable is False
    assert any("differs from deterministic" in reason for reason in result.rejection_reasons)


def test_cli_neural_safety_audit_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "neural-safety-audit",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "neural-safety-audit"
    assert payload["report_type"] == "neural_advisory_safety_audit"
    assert payload["deterministic_overall_status"] == "outside_applicability"
    assert payload["ml_is_advisory_only"] is True


def test_cli_neural_safety_audit_markdown_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "neural-safety-audit",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Neural Advisory Safety Audit" in output
    assert "Deterministic SP63 verification" in output


def test_cli_neural_safety_audit_output_file(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    output_path = tmp_path / "neural_safety_audit.md"
    capsys.readouterr()

    exit_code = main(
        [
            "neural-safety-audit",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--markdown",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert "Neural Advisory Safety Audit" in output_path.read_text(encoding="utf-8")
