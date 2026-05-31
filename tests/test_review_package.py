from sp63_core.cli import main
from sp63_core.report import (
    REVIEW_README_FILENAME,
    build_review_readme_for_batch_archive,
    build_review_readme_for_single_bundle,
)

EXAMPLE_INPUT = "docs/reports/examples/rectangular_design_input_example.json"
BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"


def test_review_readme_builder_single_contains_required_review_language(tmp_path):
    bundle_path = tmp_path / "single_bundle"
    bundle_path.mkdir()
    manifest_path = bundle_path / "manifest.json"
    manifest_path.write_text(
        (
            '{"strength_status": "pass", "serviceability_status": "pass", '
            '"overall_status": "pass"}'
        ),
        encoding="utf-8",
    )

    readme = build_review_readme_for_single_bundle(
        bundle_path=bundle_path,
        manifest_path=manifest_path,
    )

    assert "requires engineer review" in readme
    assert "ML advisory-only" in readme
    assert "report-archive-validate" in readme
    assert "report-archive-zip" in readme
    assert "strength_status: `pass`" in readme


def test_review_readme_builder_batch_contains_index_and_status_summary(tmp_path):
    archive_path = tmp_path / "batch_bundle"
    archive_path.mkdir()
    manifest_path = archive_path / "manifest.json"
    index_json_path = archive_path / "index.json"
    manifest_path.write_text('{"overall_status": "review_required"}', encoding="utf-8")
    index_json_path.write_text(
        (
            '{"cases": ['
            '{"strength_status": "pass", "serviceability_status": "pass"},'
            '{"strength_status": "pass", "serviceability_status": "fail"}'
            "]}"
        ),
        encoding="utf-8",
    )

    readme = build_review_readme_for_batch_archive(
        archive_path=archive_path,
        manifest_path=manifest_path,
        index_json_path=index_json_path,
    )

    assert "index.json" in readme
    assert "serviceability_status: `fail: 1, pass: 1`" in readme
    assert "deterministic SP63 checks mandatory" in readme


def test_design_report_bundle_writes_review_readme(tmp_path):
    output_dir = tmp_path / "single_bundle"
    assert main(
        [
            "design-report",
            "--input-json",
            EXAMPLE_INPUT,
            "--bundle-output",
            str(output_dir),
        ]
    ) == 0

    readme = (output_dir / REVIEW_README_FILENAME).read_text(encoding="utf-8")

    assert "requires engineer review" in readme
    assert "ML advisory-only" in readme
    assert "report-archive-validate" in readme


def test_batch_report_archive_writes_root_review_readme(tmp_path):
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

    readme_path = output_dir / REVIEW_README_FILENAME
    readme = readme_path.read_text(encoding="utf-8")

    assert readme_path.exists()
    assert "Batch" in readme or "batch" in readme
    assert "ML advisory-only" in readme
