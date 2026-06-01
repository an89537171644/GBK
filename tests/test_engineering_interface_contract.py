import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_engineering_interface_contract


def test_engineering_interface_contract_pass():
    result = build_engineering_interface_contract()

    assert result.status == "pass"
    assert result.contract_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert result.errors == ()


def test_engineering_interface_contract_contains_required_safety_content():
    result = build_engineering_interface_contract()

    assert "This software does not certify design decisions." in result.mandatory_warnings
    assert "ML is not a design checker." in result.mandatory_warnings
    assert "ml_ready_for_project_use must remain false." in result.mandatory_warnings
    assert "present ML result as final design decision" in result.forbidden_ui_actions
    assert "allow ml_ready_for_project_use = true" in result.forbidden_ui_actions
    assert "Start / Project Safety Notice" in result.required_screens
    assert "Engineer Acceptance Checklist" in result.required_screens


def test_engineering_interface_contract_json_data_is_machine_readable():
    result = build_engineering_interface_contract()

    assert result.json_data["contract_type"] == "engineering_gui_wrapper_contract"
    assert result.json_data["status"] == "pass"
    assert "deterministic_design_workflow" in result.json_data["workflows"]
    assert "engineering_ml_readiness" in result.json_data["workflows"]
    assert result.json_data["requires_engineer_review"] is True
    assert result.json_data["ml_is_advisory_only"] is True
    assert result.json_data["deterministic_checks_required"] is True
    assert result.json_data["ml_ready_for_project_use"] is False


def test_engineering_interface_contract_writes_output_files(tmp_path):
    result = build_engineering_interface_contract(output_dir=tmp_path)

    json_path = tmp_path / "engineering_interface_contract.json"
    markdown_path = tmp_path / "engineering_interface_contract.md"
    assert result.output_dir == str(tmp_path)
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["ml_ready_for_project_use"] is False
    assert "Engineering GUI/Desktop Wrapper Contract" in markdown_path.read_text(
        encoding="utf-8"
    )


def test_cli_engineering_interface_contract_json(tmp_path, capsys):
    output_dir = tmp_path / "contract"

    exit_code = main(
        [
            "engineering-interface-contract",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-interface-contract"
    assert payload["status"] == "pass"
    assert payload["contract_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert "workflow_self_check" in payload["workflow_names"]
    assert (output_dir / "engineering_interface_contract.json").exists()
    assert (output_dir / "engineering_interface_contract.md").exists()


def test_cli_engineering_interface_contract_markdown(tmp_path, capsys):
    output_dir = tmp_path / "contract_markdown"

    exit_code = main(
        [
            "engineering-interface-contract",
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering GUI/Desktop Wrapper Contract" in output
    assert "Forbidden UI Actions" in output
    assert "ml_ready_for_project_use = false" in output
    assert (output_dir / "engineering_interface_contract.md").exists()


def test_cli_engineering_interface_contract_no_output_files(tmp_path, capsys):
    output_dir = tmp_path / "contract_no_files"

    exit_code = main(
        [
            "engineering-interface-contract",
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


def test_engineering_interface_contract_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/interface_contract.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
