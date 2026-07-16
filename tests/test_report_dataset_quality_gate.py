import csv
import json

import pytest

from sp63_core.cli import main
from sp63_core.dataset import (
    export_dataset_from_report_archive,
    run_report_dataset_quality_gate,
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


def test_report_dataset_quality_gate_accepts_jsonl_export(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = run_report_dataset_quality_gate(dataset_path=dataset_path, min_rows=1)

    assert result.row_count == 3
    assert result.required_columns_present is True
    assert result.provenance_columns_present is True
    assert result.advisory_flags_present is True
    assert result.empty_critical_values_count == 0
    assert result.status in {"pass", "review_required"}


def test_report_dataset_quality_gate_accepts_csv_export(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    result = run_report_dataset_quality_gate(
        dataset_path=dataset_path,
        dataset_format="csv",
        min_rows=1,
    )

    assert result.row_count == 3
    assert result.required_columns_present is True
    assert result.provenance_columns_present is True
    assert result.advisory_flags_present is True


def test_report_dataset_quality_gate_fails_missing_required_column(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row.pop("M")
    broken_path = tmp_path / "missing_column.jsonl"
    _write_jsonl(broken_path, rows)

    result = run_report_dataset_quality_gate(dataset_path=broken_path, min_rows=1)

    assert result.status == "fail"
    assert "M" in result.missing_required_columns


def test_report_dataset_quality_gate_fails_empty_critical_value(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    rows[0]["b"] = ""
    broken_path = tmp_path / "empty_value.jsonl"
    _write_jsonl(broken_path, rows)

    result = run_report_dataset_quality_gate(dataset_path=broken_path, min_rows=1)

    assert result.status == "fail"
    assert result.empty_critical_values_count == 1


def test_report_dataset_quality_gate_small_dataset_requires_review(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = run_report_dataset_quality_gate(dataset_path=dataset_path, min_rows=100)

    assert result.status == "review_required"
    assert any("row count" in warning for warning in result.warnings)


def test_report_dataset_quality_gate_reports_leakage_columns(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)

    result = run_report_dataset_quality_gate(dataset_path=dataset_path, min_rows=1)

    assert "bending_status" in result.leakage_columns_detected
    assert "overall_status" not in result.leakage_columns_detected
    assert any("status/check result columns" in warning for warning in result.warnings)


def test_report_dataset_quality_gate_fails_missing_advisory_flags(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    for row in rows:
        row.pop("requires_engineer_review")
    broken_path = tmp_path / "missing_flags.jsonl"
    _write_jsonl(broken_path, rows)

    result = run_report_dataset_quality_gate(dataset_path=broken_path, min_rows=1)

    assert result.status == "fail"
    assert result.advisory_flags_present is False


def test_report_dataset_quality_gate_fails_nonpassing_archive_status(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    rows[0]["archive_validation_status"] = "fail"
    broken_path = tmp_path / "archive_fail.jsonl"
    _write_jsonl(broken_path, rows)

    result = run_report_dataset_quality_gate(dataset_path=broken_path, min_rows=1)

    assert result.status == "fail"
    assert any("archive_validation_status" in error for error in result.errors)


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "error_text"),
    (
        ("dataset_version", "0.2", "dataset_version"),
        ("local_axes_id", "", "orientation provenance"),
        ("moment_axis", "local_y", "orientation provenance"),
        ("tension_face", "unknown", "orientation provenance"),
        ("load_duration", "long", "load_duration must be short"),
        ("completeness_status", "complete", "hard safety statuses"),
        ("evidence_status", "confirmed", "hard safety statuses"),
        ("project_use_status", "allowed", "hard safety statuses"),
        ("project_use", True, "hard safety statuses"),
        ("requires_engineer_review", False, "hard safety statuses"),
    ),
)
def test_report_dataset_quality_gate_rejects_unsafe_provenance(
    tmp_path,
    field_name,
    invalid_value,
    error_text,
):
    dataset_path = _write_batch_dataset(tmp_path)
    rows = _read_jsonl(dataset_path)
    rows[0][field_name] = invalid_value
    broken_path = tmp_path / f"invalid_{field_name}.jsonl"
    _write_jsonl(broken_path, rows)

    result = run_report_dataset_quality_gate(dataset_path=broken_path, min_rows=1)

    assert result.status == "fail"
    assert any(error_text in error for error in result.errors)


def test_cli_report_dataset_quality_json_output(tmp_path, capsys):
    dataset_path = _write_batch_dataset(tmp_path)
    capsys.readouterr()

    exit_code = main(
        [
            "report-dataset-quality",
            "--dataset",
            str(dataset_path),
            "--json",
            "--min-rows",
            "1",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-dataset-quality"
    assert payload["row_count"] == 3
    assert payload["required_columns_present"] is True


def test_report_dataset_quality_gate_csv_loader_reads_strings(tmp_path):
    dataset_path = _write_batch_dataset(tmp_path, output_format="csv")

    with dataset_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert rows
    assert rows[0]["requires_engineer_review"] == "True"
