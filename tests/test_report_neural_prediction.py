import json

from sp63_core.cli import main
from sp63_core.dataset import export_dataset_from_report_archive
from sp63_core.ml import build_neural_advisory_prediction

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


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_report_neural_predict_builds_from_jsonl(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.status == "review_required"
    assert result.target == "overall_status"
    assert result.predicted_status in {"fail", "pass", "review_or_fail"}
    assert result.prediction_confidence is not None
    assert result.class_probabilities
    assert result.deterministic_strength_status == "pass"
    assert result.deterministic_serviceability_status == "pass"
    assert result.deterministic_overall_status == "pass"
    assert result.deterministic_report_required is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.requires_engineer_review is True
    assert result.neural_network_used is True


def test_report_neural_predict_builds_from_csv(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        dataset_format="csv",
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.predicted_status in {"fail", "pass", "review_or_fail"}
    assert result.deterministic_overall_status == "pass"
    assert result.neural_network_used is True


def test_report_neural_predict_does_not_use_leakage_columns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert "bending_status" not in result.feature_columns
    assert "strength_status" not in result.feature_columns
    assert "overall_status" not in result.feature_columns
    assert "Mult" not in result.feature_columns
    assert "Qult" not in result.feature_columns
    assert "bending_status" in result.excluded_leakage_columns
    assert "Mult" in result.excluded_leakage_columns


def test_report_neural_predict_small_dataset_requires_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        max_iter=50,
    )

    assert result.status == "review_required"
    assert any("too small" in warning for warning in result.warnings)
    assert any("not production evidence" in warning for warning in result.warnings)


def test_report_neural_predict_missing_target_fails(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row.pop("overall_status")
    missing_path = tmp_path / "missing_target.jsonl"
    _write_jsonl(missing_path, rows)

    result = build_neural_advisory_prediction(
        dataset_path=missing_path,
        input_json_path=INPUT_JSON,
    )

    assert result.status == "fail"
    assert "target column is missing: overall_status" in result.errors
    assert result.predicted_status is None
    assert result.neural_network_used is False


def test_report_neural_predict_deterministic_derived_warns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
        feature_mode="deterministic_derived",
        max_iter=50,
    )

    assert "h0" in result.feature_columns
    assert "longitudinal_as_mm2" in result.feature_columns
    assert any(
        "deterministic-derived features may leak design decisions" in warning
        for warning in result.warnings
    )


def test_report_neural_predict_mismatch_requires_review(tmp_path, monkeypatch):
    dataset_path = _write_batch_dataset(tmp_path)

    def fake_train_and_predict_status(**_kwargs):
        return "fail", 0.99, {"fail": 0.99, "pass": 0.01}, True, None

    monkeypatch.setattr(
        "sp63_core.ml.report_neural_prediction._train_and_predict_status",
        fake_train_and_predict_status,
    )

    result = build_neural_advisory_prediction(
        dataset_path=dataset_path,
        input_json_path=INPUT_JSON,
    )

    assert result.deterministic_overall_status == "pass"
    assert result.predicted_status == "fail"
    assert result.prediction_matches_deterministic is False
    assert result.status == "review_required"
    assert any("differs from deterministic" in warning for warning in result.warnings)


def test_cli_report_neural_predict_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "report-neural-predict",
            "--dataset",
            str(dataset_path),
            "--input-json",
            INPUT_JSON,
            "--max-iter",
            "50",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-neural-predict"
    assert payload["target"] == "overall_status"
    assert payload["deterministic_overall_status"] == "pass"
    assert payload["deterministic_report_required"] is True
    assert payload["ml_is_advisory_only"] is True
    assert payload["deterministic_checks_required"] is True
    assert payload["requires_engineer_review"] is True
