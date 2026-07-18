import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_external_validation_evidence_package

SAMPLE_CSV = Path("docs/validation/samples/external_validation_filled_sample.csv")


def test_external_validation_evidence_package_without_csv_is_review_required(tmp_path):
    output_dir = tmp_path / "external_evidence"

    result = build_external_validation_evidence_package(output_dir=output_dir)

    assert result.status == "review_required"
    assert result.evidence_status == "review_required"
    assert result.total_cases == 0
    assert result.accepted_cases == 0
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert "external validation CSV was not provided" in " ".join(result.warnings)
    assert Path(result.template_path).exists()
    assert Path(result.checklist_path).exists()
    assert Path(result.summary_json_path).exists()
    assert Path(result.summary_markdown_path).exists()
    assert Path(result.manifest_path).exists()


def test_external_validation_evidence_package_with_sample_requires_review(tmp_path):
    output_dir = tmp_path / "external_evidence_sample"

    result = build_external_validation_evidence_package(
        output_dir=output_dir,
        external_validation_csv=SAMPLE_CSV,
        strict_mode=True,
    )

    assert result.status == "review_required"
    assert result.evidence_status == "review_required"
    assert result.source_csv_path == str(SAMPLE_CSV)
    assert result.strict_mode is True
    assert result.total_cases == 6
    assert result.accepted_cases == 6
    assert result.review_cases == 0
    assert result.failed_cases == 0
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    assert payload["summary"]["status"] == "review_required"
    assert payload["ml_ready_for_project_use"] is False


def test_external_validation_evidence_manifest_has_checksums(tmp_path):
    output_dir = tmp_path / "external_evidence_manifest"

    result = build_external_validation_evidence_package(output_dir=output_dir)
    payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "external_validation_evidence_manifest"
    assert payload["status"] == "review_required"
    assert payload["requires_engineer_review"] is True
    relative_paths = {file_info["relative_path"] for file_info in payload["files"]}
    assert "external_validation_engineer_input_template.csv" in relative_paths
    assert "external_validation_engineer_checklist.md" in relative_paths
    assert "external_validation_evidence_summary.json" in relative_paths
    assert all(len(file_info["sha256"]) == 64 for file_info in payload["files"])


def test_cli_external_validation_evidence_package_json(tmp_path, capsys):
    output_dir = tmp_path / "external_evidence_cli"

    exit_code = main(
        [
            "external-validation-evidence-package",
            "--output-dir",
            str(output_dir),
            "--external-validation-csv",
            str(SAMPLE_CSV),
            "--strict",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "external-validation-evidence-package"
    assert payload["status"] == "review_required"
    assert payload["total_cases"] == 6
    assert payload["accepted_cases"] == 6
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["manifest_path"]).exists()
