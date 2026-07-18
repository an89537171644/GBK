import json

from sp63_core.cli import main
from sp63_core.dataset import export_dataset_from_report_archive
from sp63_core.ml import build_report_baseline_ml_result

BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"


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


def test_report_ml_baseline_builds_from_jsonl(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_baseline_ml_result(dataset_path=dataset_path)

    assert result.row_count == 3
    assert result.feature_mode == "input_only"
    assert result.target == "overall_status"
    assert result.target_distribution == {"outside_applicability": 3}
    assert result.model_name == "not_run"
    assert result.metrics == {}
    assert result.neural_network_used is False
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.requires_engineer_review is True


def test_report_ml_baseline_builds_from_csv(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = build_report_baseline_ml_result(
        dataset_path=dataset_path,
        dataset_format="csv",
    )

    assert result.row_count == 3
    assert result.target_distribution == {"outside_applicability": 3}
    assert result.metrics == {}


def test_report_ml_baseline_input_only_excludes_leakage_columns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_baseline_ml_result(dataset_path=dataset_path)

    assert "bending_status" not in result.feature_columns
    assert "strength_status" not in result.feature_columns
    assert "overall_status" not in result.feature_columns
    assert "Mult" not in result.feature_columns
    assert "Qult" not in result.feature_columns
    assert "bending_status" in result.excluded_leakage_columns
    assert "Mult" in result.excluded_leakage_columns


def test_report_ml_baseline_deterministic_derived_features_warn(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_baseline_ml_result(
        dataset_path=dataset_path,
        feature_mode="deterministic_derived",
    )

    assert "h0" in result.feature_columns
    assert "longitudinal_as_mm2" in result.feature_columns
    assert "Mult" not in result.feature_columns
    assert any(
        "deterministic-derived features may leak design decisions" in warning
        for warning in result.warnings
    )


def test_report_ml_baseline_small_dataset_requires_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_baseline_ml_result(dataset_path=dataset_path)

    assert result.status == "review_required"
    assert any("too small" in warning for warning in result.warnings)


def test_report_ml_baseline_missing_target_fails(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row.pop("overall_status")
    missing_path = tmp_path / "missing_target.jsonl"
    _write_jsonl(missing_path, rows)

    result = build_report_baseline_ml_result(dataset_path=missing_path)

    assert result.status == "fail"
    assert "target column is missing: overall_status" in result.errors
    assert result.metrics == {}


def test_report_ml_baseline_rejects_public_pass_target_while_ed01_open(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row["overall_status"] = "pass"
    constant_path = tmp_path / "constant_target.jsonl"
    _write_jsonl(constant_path, rows)

    result = build_report_baseline_ml_result(dataset_path=constant_path)

    assert result.status == "fail"
    assert result.target_distribution == {"pass": 3}
    assert result.metrics == {}
    assert "ED-01 public report-dataset contract is invalid" in result.errors


def test_cli_report_ml_baseline_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "report-ml-baseline",
            "--dataset",
            str(dataset_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-ml-baseline"
    assert payload["row_count"] == 3
    assert payload["target"] == "overall_status"
    assert payload["neural_network_used"] is False
