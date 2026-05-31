import json
import zipfile

from sp63_core.cli import main
from sp63_core.report import (
    compute_zip_sha256,
    export_report_archive_to_zip,
    validate_report_zip,
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


def test_single_report_bundle_exports_to_zip(tmp_path):
    source_dir = tmp_path / "single_bundle"
    zip_path = tmp_path / "single_bundle.zip"
    assert _write_single_bundle(source_dir) == 0

    result = export_report_archive_to_zip(source_path=source_dir, zip_path=zip_path)

    assert result.status == "pass"
    assert result.validation_status == "pass"
    assert result.file_count >= 5
    assert result.zip_sha256
    assert result.zip_sha256 == compute_zip_sha256(zip_path)
    assert result.requires_engineer_review is True
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert {"report.md", "report.json", "report.html", "input.json"}.issubset(names)


def test_batch_report_archive_exports_to_zip(tmp_path):
    source_dir = tmp_path / "batch_bundle"
    zip_path = tmp_path / "batch_bundle.zip"
    assert _write_batch_archive(source_dir) == 0

    result = export_report_archive_to_zip(source_path=source_dir, zip_path=zip_path)

    assert result.status == "pass"
    assert result.validation_status == "pass"
    assert result.file_count >= 17
    assert result.zip_sha256
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert {"manifest.json", "index.md", "index.json"}.issubset(names)
    assert "case_001/manifest.json" in names
    assert "case_001/report.md" in names
    assert "case_001/report.json" in names
    assert "case_001/report.html" in names
    assert "case_001/input.json" in names


def test_validate_report_zip_detects_path_traversal(tmp_path):
    zip_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("manifest.json", "{}")
        archive.writestr("../escape.txt", "unsafe")

    result = validate_report_zip(zip_path)

    assert result.status == "fail"
    assert result.validation_status == "fail"
    assert any("unsafe ZIP entry path" in error for error in result.errors)
    assert result.requires_engineer_review is True


def test_cli_report_archive_zip_single_json(tmp_path, capsys):
    source_dir = tmp_path / "single_bundle"
    zip_path = tmp_path / "single_bundle.zip"
    assert _write_single_bundle(source_dir) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "report-archive-zip",
            "--path",
            str(source_dir),
            "--output",
            str(zip_path),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-archive-zip"
    assert payload["status"] == "pass"
    assert payload["validation_status"] == "pass"
    assert payload["zip_sha256"]
    assert payload["requires_engineer_review"] is True


def test_cli_report_archive_zip_batch_json(tmp_path, capsys):
    source_dir = tmp_path / "batch_bundle"
    zip_path = tmp_path / "batch_bundle.zip"
    assert _write_batch_archive(source_dir) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "report-archive-zip",
            "--path",
            str(source_dir),
            "--output",
            str(zip_path),
            "--batch",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-archive-zip"
    assert payload["status"] == "pass"
    assert payload["validation_status"] == "pass"
    assert payload["file_count"] >= 17
    assert payload["zip_sha256"]
