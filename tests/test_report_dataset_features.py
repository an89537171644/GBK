import json

from sp63_core.cli import main
from sp63_core.dataset import (
    build_report_dataset_feature_set,
    export_dataset_from_report_archive,
)

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


def test_report_dataset_feature_set_builds_from_jsonl(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(dataset_path=dataset_path)

    assert result.row_count == 3
    assert result.target == "overall_status"
    assert result.target_distribution == {"fail": 1, "pass": 1, "review_or_fail": 1}
    assert result.feature_count == len(result.feature_columns)
    assert result.train_count + result.validation_count + result.test_count == result.row_count
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True


def test_report_dataset_feature_set_builds_from_csv(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = build_report_dataset_feature_set(
        dataset_path=dataset_path,
        dataset_format="csv",
    )

    assert result.row_count == 3
    assert result.target_distribution == {"fail": 1, "pass": 1, "review_or_fail": 1}
    assert "b" in result.feature_columns


def test_input_only_excludes_status_and_check_leakage_columns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(dataset_path=dataset_path)

    assert "bending_status" not in result.feature_columns
    assert "strength_status" not in result.feature_columns
    assert "overall_status" not in result.feature_columns
    assert "Mult" not in result.feature_columns
    assert "Qult" not in result.feature_columns
    assert "bending_status" in result.excluded_leakage_columns
    assert "Mult" in result.excluded_leakage_columns


def test_deterministic_derived_features_warn_about_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(
        dataset_path=dataset_path,
        feature_mode="deterministic_derived",
    )

    assert "h0" in result.feature_columns
    assert "longitudinal_as_mm2" in result.feature_columns
    assert "Mult" not in result.feature_columns
    assert any("deterministic-derived features" in warning for warning in result.warnings)


def test_report_dataset_features_recognizes_overall_status_target(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(dataset_path=dataset_path, target="overall_status")

    assert result.target_columns == ("overall_status",)
    assert result.status == "review_required"
    assert result.target_distribution["pass"] == 1


def test_report_dataset_features_constant_target_requires_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row["overall_status"] = "pass"
    constant_path = tmp_path / "constant_target.jsonl"
    _write_jsonl(constant_path, rows)

    result = build_report_dataset_feature_set(dataset_path=constant_path)

    assert result.status == "review_required"
    assert result.target_distribution == {"pass": 3}
    assert any("constant" in warning for warning in result.warnings)


def test_report_dataset_features_missing_target_fails(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row.pop("overall_status")
    missing_path = tmp_path / "missing_target.jsonl"
    _write_jsonl(missing_path, rows)

    result = build_report_dataset_feature_set(dataset_path=missing_path)

    assert result.status == "fail"
    assert "target column is missing: overall_status" in result.errors


def test_report_dataset_features_small_dataset_requires_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(dataset_path=dataset_path)

    assert result.status == "review_required"
    assert any("too small" in warning for warning in result.warnings)


def test_report_dataset_features_split_counts_sum_to_rows(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = build_report_dataset_feature_set(dataset_path=dataset_path)

    assert result.train_count + result.validation_count + result.test_count == result.row_count
    assert result.split_strategy == "source_archive_path_case_id"


def test_cli_report_dataset_features_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "report-dataset-features",
            "--dataset",
            str(dataset_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-dataset-features"
    assert payload["row_count"] == 3
    assert payload["target"] == "overall_status"
