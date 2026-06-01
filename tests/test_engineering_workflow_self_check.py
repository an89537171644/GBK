import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.dataset import REQUIRED_REPORT_DATASET_COLUMNS
from sp63_core.workflows import run_engineering_workflow_self_check

EXTERNAL_FIXTURE = Path("tests/fixtures/external_validation_sample.csv")
MATERIAL_FIXTURE = Path("tests/fixtures/material_verification_sample.csv")


def _dataset_row() -> dict[str, object]:
    row: dict[str, object] = {column: "1" for column in REQUIRED_REPORT_DATASET_COLUMNS}
    row.update(
        {
            "dataset_source": "validated_report_archive",
            "case_id": "case_001",
            "source_archive_path": "reports/case_001",
            "report_json_path": "reports/case_001/report.json",
            "input_json_path": "reports/case_001/input.json",
            "manifest_path": "reports/case_001/manifest.json",
            "input_sha256": "a" * 64,
            "report_json_sha256": "b" * 64,
            "manifest_sha256": "c" * 64,
            "archive_validation_status": "pass",
            "b": 300,
            "h": 500,
            "cover": 32,
            "concrete_class": "B25",
            "longitudinal_rebar_class": "A500",
            "stirrup_rebar_class": "A240",
            "M": 150_000_000,
            "Q": 80_000,
            "strength_status": "pass",
            "serviceability_status": "pass",
            "overall_status": "pass",
            "warnings_count": 0,
            "requires_engineer_review": True,
            "ml_is_advisory_only": True,
            "deterministic_checks_required": True,
            "external_validation_status": "not_provided",
            "material_verification_status": "not_provided",
        }
    )
    return row


def _write_jsonl_dataset(path: Path) -> Path:
    path.write_text(json.dumps(_dataset_row(), ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def test_self_check_runs_and_creates_deterministic_outputs(tmp_path):
    output_dir = tmp_path / "self_check"

    result = run_engineering_workflow_self_check(output_dir=output_dir)

    assert result.self_check_status == "pass"
    assert result.deterministic_archive_status == "pass"
    assert result.deterministic_zip_status == "pass"
    assert result.ml_ready_for_project_use is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.failed_checks == 0
    assert (output_dir / "workflow_self_check.md").exists()
    assert (output_dir / "workflow_self_check.json").exists()
    assert (output_dir / "deterministic_workflow" / "deterministic_report.zip").exists()
    assert (
        output_dir / "deterministic_workflow" / "deterministic_report" / "README_REVIEW.md"
    ).exists()


def test_self_check_with_ml_readiness_keeps_project_use_false(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_dir = tmp_path / "self_check_ml"

    result = run_engineering_workflow_self_check(
        output_dir=output_dir,
        include_ml_readiness=True,
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    assert result.self_check_status == "review_required"
    assert result.ml_workflow_status == "review_required"
    assert result.ml_ready_for_research is True
    assert result.ml_ready_for_engineering_review is True
    assert result.ml_ready_for_project_use is False
    assert (output_dir / "ml_workflow" / "ml_readiness" / "README_REVIEW.md").exists()


def test_self_check_ml_requested_without_dataset_is_review_required(tmp_path):
    output_dir = tmp_path / "self_check_missing_dataset"

    result = run_engineering_workflow_self_check(
        output_dir=output_dir,
        include_ml_readiness=True,
    )

    assert result.self_check_status == "review_required"
    assert result.ml_workflow_status == "not_run"
    assert "ML readiness requested but dataset_path was not provided" in result.warnings


def test_self_check_cleanup_removes_temporary_workflow_outputs(tmp_path):
    output_dir = tmp_path / "self_check_cleanup"

    result = run_engineering_workflow_self_check(output_dir=output_dir, cleanup=True)

    assert result.self_check_status == "pass"
    assert (output_dir / "workflow_self_check.md").exists()
    assert not (output_dir / "deterministic_workflow").exists()


def test_cli_engineering_workflow_self_check_json(tmp_path, capsys):
    output_dir = tmp_path / "self_check_cli"

    exit_code = main(
        [
            "engineering-workflow-self-check",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-workflow-self-check"
    assert payload["self_check_status"] == "pass"
    assert payload["deterministic_archive_status"] == "pass"
    assert payload["deterministic_zip_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False


def test_cli_engineering_workflow_self_check_markdown(tmp_path, capsys):
    output_dir = tmp_path / "self_check_cli_markdown"

    exit_code = main(
        [
            "engineering-workflow-self-check",
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering Workflow Self-Check" in output
    assert "deterministic_archive_status" in output
