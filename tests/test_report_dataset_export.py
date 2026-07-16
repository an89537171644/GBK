import csv
import json

import pytest

from sp63_core.cli import main
from sp63_core.dataset import (
    DATASET_VERSION,
    REPORT_DATASET_SOURCE,
    export_dataset_from_report_archive,
    extract_dataset_row_from_report_json,
)

EXAMPLE_INPUT = "docs/reports/examples/rectangular_design_input_example.json"
BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"


def _write_single_bundle(output_dir) -> int:
    return main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--bundle-output",
            str(output_dir),
        ]
    )


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


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_single_report_bundle_exports_dataset_jsonl(tmp_path):
    source_dir = tmp_path / "single_bundle"
    output_path = tmp_path / "single_dataset.jsonl"
    assert _write_single_bundle(source_dir) == 0

    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
    )

    rows = _read_jsonl(output_path)
    assert result.status == "pass"
    assert result.row_count == 1
    assert result.archive_validation_status == "pass"
    assert rows[0]["dataset_source"] == REPORT_DATASET_SOURCE
    assert rows[0]["dataset_version"] == DATASET_VERSION
    assert rows[0]["local_axes_id"] == "example-section-local-axes"
    assert rows[0]["moment_axis"] == "local_z"
    assert rows[0]["tension_face"] == "local_y_min"
    assert rows[0]["load_duration"] == "short"
    assert rows[0]["completeness_status"] == "incomplete"
    assert rows[0]["evidence_status"] == "needs_engineer_review"
    assert rows[0]["project_use_status"] == "prohibited"
    assert rows[0]["project_use"] is False
    assert rows[0]["requires_engineer_review"] is True
    assert rows[0]["ml_is_advisory_only"] is True
    assert rows[0]["deterministic_checks_required"] is True
    assert rows[0]["archive_validation_status"] == "pass"
    assert rows[0]["overall_status"] == "pass"
    assert rows[0]["input_sha256"]
    assert rows[0]["report_json_sha256"]
    assert rows[0]["manifest_sha256"]


def test_batch_report_archive_exports_dataset_jsonl(tmp_path):
    source_dir = tmp_path / "batch_bundle"
    output_path = tmp_path / "batch_dataset.jsonl"
    assert _write_batch_archive(source_dir) == 0

    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
    )

    rows = _read_jsonl(output_path)
    assert result.status == "pass"
    assert result.row_count == 3
    assert len(rows) == 3
    assert {row["case_id"] for row in rows} == {"case_001", "case_002", "case_003"}
    assert all(row["dataset_source"] == REPORT_DATASET_SOURCE for row in rows)
    assert all(row["dataset_version"] == DATASET_VERSION for row in rows)
    assert all(row["local_axes_id"] for row in rows)
    assert all(row["moment_axis"] == "local_z" for row in rows)
    assert all(row["tension_face"] == "local_y_min" for row in rows)
    assert all(row["load_duration"] == "short" for row in rows)
    assert all(row["project_use"] is False for row in rows)
    assert all(row["requires_engineer_review"] is True for row in rows)
    assert all(row["ml_is_advisory_only"] is True for row in rows)
    assert all(row["deterministic_checks_required"] is True for row in rows)


def test_batch_report_archive_exports_dataset_csv(tmp_path):
    source_dir = tmp_path / "batch_bundle"
    output_path = tmp_path / "batch_dataset.csv"
    assert _write_batch_archive(source_dir) == 0

    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
        output_format="csv",
    )

    with output_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert result.status == "pass"
    assert result.row_count == 3
    assert len(rows) == 3
    assert rows[0]["dataset_source"] == REPORT_DATASET_SOURCE
    assert rows[0]["dataset_version"] == DATASET_VERSION
    assert rows[0]["local_axes_id"]
    assert rows[0]["moment_axis"] == "local_z"
    assert rows[0]["tension_face"] == "local_y_min"
    assert rows[0]["load_duration"] == "short"
    assert rows[0]["completeness_status"] == "incomplete"
    assert rows[0]["evidence_status"] == "needs_engineer_review"
    assert rows[0]["project_use_status"] == "prohibited"
    assert rows[0]["project_use"] == "False"
    assert rows[0]["overall_status"]
    assert "strength_status" in rows[0]
    assert "serviceability_status" in rows[0]


def test_report_dataset_extraction_rejects_long_duration(tmp_path):
    source_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(source_dir) == 0
    input_path = source_dir / "input.json"
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload["load_duration"] = "long"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="load_duration"):
        extract_dataset_row_from_report_json(source_dir / "report.json")


def test_report_dataset_extraction_rejects_unsafe_hard_status(tmp_path):
    source_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(source_dir) == 0
    report_path = source_dir / "report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["project_use"] = True
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="project_use"):
        extract_dataset_row_from_report_json(report_path)


def test_invalid_report_archive_does_not_export_dataset(tmp_path):
    source_dir = tmp_path / "single_bundle"
    output_path = tmp_path / "single_dataset.jsonl"
    assert _write_single_bundle(source_dir) == 0
    (source_dir / "README_REVIEW.md").unlink()

    result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=output_path,
    )

    assert result.status == "fail"
    assert result.row_count == 0
    assert result.archive_validation_status == "fail"
    assert not output_path.exists()
    assert any("README_REVIEW.md" in error for error in result.errors)


def test_cli_report_dataset_export_single_json(tmp_path, capsys):
    source_dir = tmp_path / "single_bundle"
    output_path = tmp_path / "single_dataset.jsonl"
    assert _write_single_bundle(source_dir) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "report-dataset-export",
            "--path",
            str(source_dir),
            "--output",
            str(output_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-dataset-export"
    assert payload["status"] == "pass"
    assert payload["row_count"] == 1
    assert output_path.exists()


def test_cli_report_dataset_export_batch_csv_json(tmp_path, capsys):
    source_dir = tmp_path / "batch_bundle"
    output_path = tmp_path / "batch_dataset.csv"
    assert _write_batch_archive(source_dir) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "report-dataset-export",
            "--path",
            str(source_dir),
            "--batch",
            "--output",
            str(output_path),
            "--format",
            "csv",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-dataset-export"
    assert payload["status"] == "pass"
    assert payload["row_count"] == 3
    assert output_path.exists()
