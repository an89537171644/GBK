import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_project_template_package


def test_project_template_package_creates_expected_files(tmp_path):
    result = build_project_template_package(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert (tmp_path / "input" / "rectangular_input.json").exists()
    assert (tmp_path / "evidence" / "external_validation_template.csv").exists()
    assert (tmp_path / "evidence" / "material_verification_template.csv").exists()
    assert (tmp_path / "README_PROJECT_TEMPLATE.md").exists()
    assert (tmp_path / "RUN_COMMANDS.md").exists()
    assert (tmp_path / "acceptance_checklist.md").exists()
    assert (tmp_path / "project_template_manifest.json").exists()


def test_project_template_manifest_contains_sha256_and_relative_paths(tmp_path):
    build_project_template_package(output_dir=tmp_path)

    manifest = json.loads(
        (tmp_path / "project_template_manifest.json").read_text(encoding="utf-8")
    )

    relative_paths = {file_info["relative_path"] for file_info in manifest["files"]}
    assert manifest["report_type"] == "project_template_manifest"
    assert manifest["ml_ready_for_project_use"] is False
    assert "input/rectangular_input.json" in relative_paths
    assert "evidence/external_validation_template.csv" in relative_paths
    assert "evidence/material_verification_template.csv" in relative_paths
    assert all(len(file_info["sha256"]) == 64 for file_info in manifest["files"])


def test_project_template_readme_and_checklist_contain_safety_warnings(tmp_path):
    build_project_template_package(output_dir=tmp_path)

    readme = (tmp_path / "README_PROJECT_TEMPLATE.md").read_text(encoding="utf-8")
    checklist = (tmp_path / "acceptance_checklist.md").read_text(encoding="utf-8")
    commands = (tmp_path / "RUN_COMMANDS.md").read_text(encoding="utf-8")

    assert "does not certify" in readme
    assert "ml_ready_for_project_use = false" in readme
    assert "No full SP 63 text" in checklist
    assert "ML outputs" in checklist
    assert "engineering-workflow" in commands
    assert "external-validation" in commands


def test_cli_project_template_json(tmp_path, capsys):
    output_dir = tmp_path / "project_template"

    exit_code = main(["project-template", "--output-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "project-template"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "project_template_manifest.json").exists()


def test_project_template_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/project_template.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
