import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.dataset import REQUIRED_REPORT_DATASET_COLUMNS
from sp63_core.workflows import run_engineering_workflow

EXAMPLE_INPUT = Path("docs/reports/examples/rectangular_design_input_example.json")
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


def test_engineering_workflow_without_ml_creates_report_zip_and_summary(tmp_path):
    output_dir = tmp_path / "workflow"

    result = run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    deterministic_dir = output_dir / "deterministic_report"
    assert result.workflow_status == "review_required"
    assert result.deterministic_report_status == "pass"
    assert result.archive_validation_status == "pass"
    assert result.zip_status == "pass"
    assert result.ml_readiness_status is None
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    for filename in (
        "input.json",
        "report.md",
        "report.json",
        "report.html",
        "manifest.json",
        "README_REVIEW.md",
    ):
        assert (deterministic_dir / filename).exists()
    assert (output_dir / "deterministic_report.zip").exists()
    assert (output_dir / "workflow_summary.json").exists()
    assert (output_dir / "workflow_summary.md").exists()
    assert (output_dir / "README_WORKFLOW.md").exists()


def test_engineering_workflow_no_zip_skips_zip(tmp_path):
    output_dir = tmp_path / "workflow_no_zip"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        create_zip=False,
    )

    assert result.zip_status == "skipped"
    assert not (output_dir / "deterministic_report.zip").exists()
    assert result.archive_validation_status == "pass"


def test_engineering_workflow_with_ml_readiness(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_dir = tmp_path / "workflow_ml"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        include_ml_readiness=True,
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    ml_dir = output_dir / "ml_readiness"
    assert result.ml_readiness_status == "review_required"
    assert result.ml_ready_for_research is True
    assert result.ml_ready_for_engineering_review is True
    assert result.ml_ready_for_project_use is False
    assert (ml_dir / "engineering_ml_readiness.md").exists()
    assert (ml_dir / "engineering_ml_readiness.json").exists()
    assert (ml_dir / "engineering_ml_readiness_matrix.csv").exists()
    assert (ml_dir / "README_REVIEW.md").exists()


def test_engineering_workflow_ml_requested_without_dataset_is_review_required(tmp_path):
    output_dir = tmp_path / "workflow_missing_dataset"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        include_ml_readiness=True,
    )

    assert result.workflow_status == "review_required"
    assert result.ml_readiness_status == "not_run"
    assert "ML readiness requested but dataset_path was not provided" in result.warnings


def test_cli_engineering_workflow_json(tmp_path, capsys):
    output_dir = tmp_path / "workflow_cli"

    exit_code = main(
        [
            "engineering-workflow",
            "--input-json",
            str(EXAMPLE_INPUT),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-workflow"
    assert payload["deterministic_report_status"] == "pass"
    assert payload["archive_validation_status"] == "pass"
    assert payload["zip_status"] == "pass"
    assert payload["requires_engineer_review"] is True


def test_cli_engineering_workflow_markdown(tmp_path, capsys):
    output_dir = tmp_path / "workflow_cli_markdown"

    exit_code = main(
        [
            "engineering-workflow",
            "--input-json",
            str(EXAMPLE_INPUT),
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering Workflow Summary" in output
    assert "deterministic_report_status" in output
