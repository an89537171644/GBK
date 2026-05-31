import json

from sp63_core.cli import main
from sp63_core.report import validate_batch_report_archive, validate_report_bundle

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


def test_single_bundle_archive_validation_passes(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0

    result = validate_report_bundle(output_dir)

    assert result.status == "pass"
    assert result.manifest_count == 1
    assert result.checked_file_count >= 4
    assert result.missing_file_count == 0
    assert result.checksum_mismatch_count == 0
    assert result.index_consistency_status == "pass"
    assert result.requires_engineer_review is True


def test_single_bundle_archive_validation_fails_for_missing_review_readme(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    (output_dir / "README_REVIEW.md").unlink()

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert result.missing_file_count >= 1
    assert any("README_REVIEW.md" in error for error in result.errors)


def test_batch_archive_validation_passes(tmp_path):
    output_dir = tmp_path / "batch_bundle"
    assert main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    ) == 0

    result = validate_batch_report_archive(output_dir)

    assert result.status == "pass"
    assert result.manifest_count == 4
    assert result.checked_file_count >= 12
    assert result.missing_file_count == 0
    assert result.checksum_mismatch_count == 0
    assert result.index_consistency_status == "pass"
    assert result.requires_engineer_review is True


def test_batch_archive_validation_fails_for_missing_root_review_readme(tmp_path):
    output_dir = tmp_path / "batch_bundle"
    assert main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    ) == 0
    (output_dir / "README_REVIEW.md").unlink()

    result = validate_batch_report_archive(output_dir)

    assert result.status == "fail"
    assert result.missing_file_count >= 1
    assert any("README_REVIEW.md" in error for error in result.errors)


def test_report_archive_validation_fails_for_missing_file(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    (output_dir / "report.html").unlink()

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert result.missing_file_count >= 1
    assert any("missing" in error for error in result.errors)


def test_report_archive_validation_fails_for_checksum_mismatch(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    (output_dir / "report.md").write_text("tampered report\n", encoding="utf-8")

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert result.checksum_mismatch_count >= 1
    assert any("checksum mismatch" in error for error in result.errors)


def test_report_archive_validation_fails_for_missing_manifest(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    (output_dir / "manifest.json").unlink()

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert result.manifest_count == 0
    assert any("missing manifest" in error for error in result.errors)


def test_cli_report_archive_validate_single_json(tmp_path, capsys):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    capsys.readouterr()

    exit_code = main(["report-archive-validate", "--path", str(output_dir), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-archive-validate"
    assert payload["status"] == "pass"
    assert payload["requires_engineer_review"] is True


def test_cli_report_archive_validate_batch_json(tmp_path, capsys):
    output_dir = tmp_path / "batch_bundle"
    assert main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    ) == 0
    capsys.readouterr()

    exit_code = main(["report-archive-validate", "--path", str(output_dir), "--batch", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "report-archive-validate"
    assert payload["status"] == "pass"
    assert payload["manifest_count"] == 4
    assert payload["index_consistency_status"] == "pass"


def test_cli_report_archive_validate_autodetects_batch(tmp_path, capsys):
    output_dir = tmp_path / "batch_bundle"
    assert main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    ) == 0
    capsys.readouterr()

    exit_code = main(["report-archive-validate", "--path", str(output_dir), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["manifest_count"] == 4
