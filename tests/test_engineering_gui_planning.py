import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_engineering_gui_planning_decision


def test_engineering_gui_planning_decision_pass():
    result = build_engineering_gui_planning_decision()

    assert result.status == "pass"
    assert result.decision_status == "pass"
    assert result.recommended_option == "cli_first_with_static_html_reports"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert result.errors == ()


def test_engineering_gui_planning_contains_required_options_and_warnings():
    result = build_engineering_gui_planning_decision()

    assert "static_html_report_viewer" in result.considered_options
    assert "streamlit_local_app" in result.considered_options
    assert "gradio_local_app" in result.considered_options
    assert "desktop_pyside_or_pyqt" in result.considered_options
    assert "fastapi_web_backend" in result.considered_options
    assert "electron_wrapper" in result.considered_options
    assert "streamlit_local_app" in result.rejected_options
    assert "ML output must never be displayed as final design decision." in (
        result.required_safety_warnings
    )
    assert "ml_ready_for_project_use must remain false." in result.required_safety_warnings


def test_engineering_gui_planning_json_data_is_machine_readable():
    result = build_engineering_gui_planning_decision()

    assert result.json_data["decision_type"] == "engineering_gui_planning_decision"
    assert result.json_data["status"] == "pass"
    assert result.json_data["recommended_option"] == "cli_first_with_static_html_reports"
    assert "engineering-workflow-self-check" in " ".join(
        result.json_data["required_backend_commands"]
    )
    assert result.json_data["requires_engineer_review"] is True
    assert result.json_data["ml_is_advisory_only"] is True
    assert result.json_data["deterministic_checks_required"] is True
    assert result.json_data["ml_ready_for_project_use"] is False


def test_engineering_gui_planning_writes_output_files(tmp_path):
    result = build_engineering_gui_planning_decision(output_dir=tmp_path)

    json_path = tmp_path / "engineering_gui_planning_decision.json"
    markdown_path = tmp_path / "engineering_gui_planning_decision.md"
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["recommended_option"] == result.recommended_option
    assert payload["ml_ready_for_project_use"] is False
    assert "Engineering GUI Planning Decision" in markdown_path.read_text(encoding="utf-8")


def test_cli_engineering_gui_planning_json(tmp_path, capsys):
    output_dir = tmp_path / "gui_planning"

    exit_code = main(
        [
            "engineering-gui-planning",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-gui-planning"
    assert payload["status"] == "pass"
    assert payload["recommended_option"] == "cli_first_with_static_html_reports"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "engineering_gui_planning_decision.json").exists()
    assert (output_dir / "engineering_gui_planning_decision.md").exists()


def test_cli_engineering_gui_planning_markdown(tmp_path, capsys):
    output_dir = tmp_path / "gui_planning_markdown"

    exit_code = main(
        [
            "engineering-gui-planning",
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering GUI Planning Decision" in output
    assert "cli_first_with_static_html_reports" in output
    assert "ml_ready_for_project_use = false" in output
    assert (output_dir / "engineering_gui_planning_decision.md").exists()


def test_cli_engineering_gui_planning_no_output_files(tmp_path, capsys):
    output_dir = tmp_path / "gui_planning_no_files"

    exit_code = main(
        [
            "engineering-gui-planning",
            "--output-dir",
            str(output_dir),
            "--no-output-files",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["output_dir"] is None
    assert not output_dir.exists()


def test_engineering_gui_planning_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/gui_planning.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
