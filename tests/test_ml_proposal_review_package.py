import json
import zipfile

import pytest

from sp63_core.cli import main
from sp63_core.dataset import export_dataset_from_report_archive
from sp63_core.ml import build_ml_proposal_review_package
from sp63_core.report import compute_file_sha256

BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"
INPUT_JSON = "docs/reports/examples/rectangular_design_input_example.json"
REQUIRED_PACKAGE_FILES = {
    "input.json",
    "deterministic_report.md",
    "deterministic_report.json",
    "deterministic_report.html",
    "neural_safety_audit.md",
    "neural_safety_audit.json",
    "ml_proposal_package.md",
    "ml_proposal_package.json",
    "README_REVIEW.md",
    "manifest.json",
}


@pytest.fixture()
def batch_datasets(tmp_path):
    source_dir = tmp_path / "batch_bundle"
    assert (
        main(
            [
                "design-report-batch",
                "--input-dir",
                BATCH_EXAMPLES_DIR,
                "--output-dir",
                str(source_dir),
            ]
        )
        == 0
    )
    jsonl_path = tmp_path / "batch_dataset.jsonl"
    csv_path = tmp_path / "batch_dataset.csv"
    jsonl_result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=jsonl_path,
        output_format="jsonl",
    )
    csv_result = export_dataset_from_report_archive(
        source_path=source_dir,
        output_path=csv_path,
        output_format="csv",
    )
    assert jsonl_result.status == "pass"
    assert csv_result.status == "pass"
    return jsonl_path, csv_path


def _package_file_names(output_dir):
    return {path.name for path in output_dir.iterdir() if path.is_file()}


def _load_manifest(output_dir):
    return json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))


def test_ml_proposal_review_package_builds_jsonl_with_zip(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review"

    result = build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        max_iter=50,
    )

    assert result.status in {"review_required", "fail"}
    assert result.package_status in {"review_required", "fail"}
    assert result.output_dir == str(output_dir)
    assert result.zip_path == str(output_dir.with_suffix(".zip"))
    assert result.file_count == len(REQUIRED_PACKAGE_FILES)
    assert result.zip_sha256 == compute_file_sha256(output_dir.with_suffix(".zip"))
    assert result.proposal_status in {"review_required", "rejected"}
    assert result.deterministic_overall_status == "outside_applicability"
    assert result.prediction_matches_deterministic is None
    assert isinstance(result.advisory_signal_usable, bool)
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.requires_engineer_review is True
    assert _package_file_names(output_dir) >= REQUIRED_PACKAGE_FILES


def test_ml_proposal_review_package_builds_csv(batch_datasets, tmp_path):
    _jsonl_path, csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review_csv"

    result = build_ml_proposal_review_package(
        dataset_path=csv_path,
        dataset_format="csv",
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        max_iter=50,
    )

    assert result.source_dataset == str(csv_path)
    assert result.zip_path == str(output_dir.with_suffix(".zip"))
    assert (output_dir / "ml_proposal_package.json").exists()
    assert (output_dir / "neural_safety_audit.json").exists()


def test_ml_proposal_review_package_manifest_has_sha256(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review"

    build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        max_iter=50,
    )

    manifest = _load_manifest(output_dir)
    assert manifest["report_type"] == "ml_proposal_engineering_review_package"
    assert manifest["requires_engineer_review"] is True
    assert manifest["ml_is_advisory_only"] is True
    assert manifest["deterministic_checks_required"] is True
    files = {record["path"]: record for record in manifest["files"]}
    assert set(files) == REQUIRED_PACKAGE_FILES - {"manifest.json"}
    for filename, record in files.items():
        assert record["sha256"] == compute_file_sha256(output_dir / filename)
        assert record["size_bytes"] > 0


def test_ml_proposal_review_package_zip_contains_required_files(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review"

    build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        max_iter=50,
    )

    with zipfile.ZipFile(output_dir.with_suffix(".zip"), "r") as archive:
        entries = {name for name in archive.namelist() if not name.endswith("/")}
    assert entries >= REQUIRED_PACKAGE_FILES
    assert "README_REVIEW.md" in entries
    assert "manifest.json" in entries


def test_ml_proposal_review_package_no_zip(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review_nozip"

    result = build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        create_zip=False,
        max_iter=50,
    )

    assert result.zip_path is None
    assert result.zip_sha256 is None
    assert not output_dir.with_suffix(".zip").exists()
    assert result.file_count == len(REQUIRED_PACKAGE_FILES)


def test_ml_proposal_review_package_deterministic_derived_warns(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review_derived"

    result = build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        feature_mode="deterministic_derived",
        max_iter=50,
    )

    assert any(
        "deterministic-derived features may leak" in warning
        for warning in result.warnings
    )
    manifest = _load_manifest(output_dir)
    assert manifest["feature_mode"] == "deterministic_derived"


def test_ml_proposal_review_package_readme_content(batch_datasets, tmp_path):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review"

    build_ml_proposal_review_package(
        dataset_path=jsonl_path,
        input_json_path=INPUT_JSON,
        output_dir=output_dir,
        max_iter=50,
    )

    readme = (output_dir / "README_REVIEW.md").read_text(encoding="utf-8")
    assert "ML Proposal Engineering Review Package" in readme
    assert "ML proposal is advisory-only" in readme
    assert "Deterministic SP63 verification is mandatory" in readme
    assert "ZIP and manifest packaging do not certify the design" in readme


def test_cli_ml_proposal_review_package_json(batch_datasets, tmp_path, capsys):
    jsonl_path, _csv_path = batch_datasets
    output_dir = tmp_path / "ml_proposal_review"
    capsys.readouterr()

    exit_code = main(
        [
            "ml-proposal-review-package",
            "--dataset",
            str(jsonl_path),
            "--input-json",
            INPUT_JSON,
            "--output-dir",
            str(output_dir),
            "--max-iter",
            "50",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "ml-proposal-review-package"
    assert payload["output_dir"] == str(output_dir)
    assert payload["zip_path"] == str(output_dir.with_suffix(".zip"))
    assert payload["file_count"] == len(REQUIRED_PACKAGE_FILES)
    assert payload["requires_engineer_review"] is True
    assert payload["ml_is_advisory_only"] is True
    assert payload["deterministic_checks_required"] is True
