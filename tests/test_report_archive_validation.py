import json

from sp63_core.cli import main
from sp63_core.report import (
    compute_file_sha256,
    validate_batch_report_archive,
    validate_report_bundle,
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
    assert result.completeness_status == "incomplete"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use_status == "prohibited"
    assert result.project_use is False
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


def test_report_archive_validation_rejects_tampered_project_use_contract(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["project_use"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert any("project_use must be false" in error for error in result.errors)


def test_report_archive_validation_rejects_stale_manifest_schema(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0
    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["manifest_version"] = "1"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert any("manifest_version must be '2'" in error for error in result.errors)


def test_report_archive_validation_rejects_self_consistent_public_bending_pass(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert _write_single_bundle(output_dir) == 0

    report_path = output_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for container in (report, report["report"], report["report"]["protocol"]):
        container["status"] = "pass"
        container["strength_status"] = "pass"
        container["overall_status"] = "pass"
        bending = container["checks"]["bending"]
        bending.update(
            {
                "status": "pass",
                "public_status": "pass",
                "Mult": 123_456.0,
                "utilization": 0.5,
                "capacity_applicable": True,
                "capacity_publication_allowed": True,
            }
        )
    report_path.write_text(json.dumps(report), encoding="utf-8")

    manifest_path = output_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["output_files"]:
        if record["path"].endswith("report.json"):
            record["sha256"] = compute_file_sha256(report_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_report_bundle(output_dir)

    assert result.status == "fail"
    assert result.checksum_mismatch_count == 0
    assert any("ED-01 contract" in error for error in result.errors)
    assert any("bending.Mult must be null" in error for error in result.errors)


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
