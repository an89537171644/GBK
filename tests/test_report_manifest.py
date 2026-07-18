import hashlib
import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.report import compute_file_sha256

EXAMPLE_INPUT = "docs/reports/examples/rectangular_design_input_example.json"
BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"


def test_compute_file_sha256_is_stable(tmp_path):
    path = tmp_path / "artifact.txt"
    path.write_bytes(b"stable content\n")

    expected = hashlib.sha256(b"stable content\n").hexdigest()
    assert compute_file_sha256(path) == expected
    assert compute_file_sha256(path) == expected


def test_single_design_report_bundle_writes_manifest(tmp_path):
    output_dir = tmp_path / "single_bundle"
    exit_code = main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--bundle-output",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["report_type"] == "rectangular_design_calculation_report"
    assert manifest["manifest_version"] == "2"
    assert manifest["command"] == "design-report"
    assert manifest["requires_engineer_review"] is True
    assert manifest["completeness_status"] == "incomplete"
    assert manifest["evidence_status"] == "needs_engineer_review"
    assert manifest["project_use_status"] == "prohibited"
    assert manifest["project_use"] is False
    assert manifest["strength_status"] == "outside_applicability"
    assert manifest["serviceability_status"] in {"pass", "fail", "review_or_fail"}
    input_files = {item["path"]: item["sha256"] for item in manifest["input_files"]}
    output_files = {item["path"]: item["sha256"] for item in manifest["output_files"]}
    assert str(Path(EXAMPLE_INPUT)) in input_files
    for name in ("report.md", "report.json", "report.html", "input.json", "README_REVIEW.md"):
        path = output_dir / name
        assert str(path) in output_files
        assert output_files[str(path)] == compute_file_sha256(path)
    readme = (output_dir / "README_REVIEW.md").read_text(encoding="utf-8")
    assert "manifest_version: `2`" in readme
    assert "completeness_status: `incomplete`" in readme
    assert "evidence_status: `needs_engineer_review`" in readme
    assert "project_use_status: `prohibited`" in readme
    assert "project_use: `false`" in readme
    assert "requires_engineer_review: `true`" in readme


def test_batch_design_report_writes_root_and_case_manifests(tmp_path):
    output_dir = tmp_path / "batch_bundle"
    exit_code = main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    assert exit_code == 0
    root_manifest_path = output_dir / "manifest.json"
    assert root_manifest_path.exists()
    root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
    assert root_manifest["report_type"] == "batch_design_report_index"
    assert root_manifest["metadata"]["case_count"] == 3
    assert root_manifest["requires_engineer_review"] is True
    assert root_manifest["manifest_version"] == "2"
    assert root_manifest["project_use_status"] == "prohibited"
    assert root_manifest["project_use"] is False
    root_output_files = {item["path"]: item["sha256"] for item in root_manifest["output_files"]}
    readme_path = output_dir / "README_REVIEW.md"
    assert str(readme_path) in root_output_files
    assert root_output_files[str(readme_path)] == compute_file_sha256(readme_path)
    readme = readme_path.read_text(encoding="utf-8")
    assert "manifest_version: `2`" in readme
    assert "completeness_status: `incomplete`" in readme
    assert "evidence_status: `needs_engineer_review`" in readme
    assert "project_use_status: `prohibited`" in readme
    assert "project_use: `false`" in readme
    assert "requires_engineer_review: `true`" in readme

    index = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    assert index["manifest_path"] == str(root_manifest_path)
    for case in index["cases"]:
        manifest_path = Path(case["manifest_path"])
        assert manifest_path.exists()
        assert manifest_path.name == "manifest.json"
        case_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert case_manifest["project_use_status"] == "prohibited"
        assert case_manifest["project_use"] is False
        assert case["input_sha256"]
        assert case["report_json_sha256"]
        assert case["report_markdown_sha256"]
        assert case["report_html_sha256"]
        assert case["report_json_sha256"] == compute_file_sha256(
            manifest_path.parent / "report.json"
        )


def test_design_report_bundle_can_skip_manifest(tmp_path):
    output_dir = tmp_path / "single_bundle_no_manifest"
    exit_code = main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--bundle-output",
            str(output_dir),
            "--no-manifest",
        ]
    )

    assert exit_code == 0
    assert not (output_dir / "manifest.json").exists()
