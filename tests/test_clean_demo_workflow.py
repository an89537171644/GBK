import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import CLEAN_DEMO_INPUT, run_clean_demo_workflow, run_input_preflight


def test_clean_demo_input_preflight_passes():
    result = run_input_preflight(CLEAN_DEMO_INPUT)

    assert result.status == "pass"
    assert result.preflight_status == "pass"
    assert result.error_count == 0
    assert result.requires_engineer_review is True
    assert result.ml_ready_for_project_use is False


def test_clean_demo_workflow_runs_deterministic_pass(tmp_path):
    output_dir = tmp_path / "clean_demo"

    result = run_clean_demo_workflow(output_dir=output_dir)

    assert result.status == "pass"
    assert result.demo_status == "pass"
    assert result.workflow_status == "review_required"
    assert result.preflight_status == "pass"
    assert result.deterministic_report_status == "pass"
    assert result.archive_validation_status == "pass"
    assert result.zip_status == "pass"
    assert result.index_status == "pass"
    assert result.index_path is not None
    assert Path(result.index_path).exists()
    assert result.errors == ()
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert (output_dir / "clean_demo_workflow.json").exists()
    assert (output_dir / "clean_demo_workflow.md").exists()
    assert (output_dir / "deterministic_report.zip").exists()
    assert (output_dir / "deterministic_report" / "README_REVIEW.md").exists()


def test_cli_clean_demo_workflow_json(tmp_path, capsys):
    output_dir = tmp_path / "clean_demo_cli"

    exit_code = main(
        [
            "clean-demo-workflow",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "clean-demo-workflow"
    assert payload["status"] == "pass"
    assert payload["demo_status"] == "pass"
    assert payload["preflight_status"] == "pass"
    assert payload["deterministic_report_status"] == "pass"
    assert payload["archive_validation_status"] == "pass"
    assert payload["zip_status"] == "pass"
    assert payload["index_status"] == "pass"
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False


def test_cli_clean_demo_workflow_markdown(tmp_path, capsys):
    output_dir = tmp_path / "clean_demo_cli_markdown"

    exit_code = main(
        [
            "clean-demo-workflow",
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Clean Deterministic Demo Workflow" in output
    assert "demo_status: `pass`" in output
    assert "ml_ready_for_project_use = false" in output
