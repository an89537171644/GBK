import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_engineering_handoff_package


def test_engineering_handoff_package_creates_expected_files(tmp_path):
    output_dir = tmp_path / "handoff"

    result = build_engineering_handoff_package(output_dir=output_dir)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert result.file_count >= 10
    for path_text in (
        result.input_json_path,
        result.clean_demo_input_path,
        result.external_validation_template_path,
        result.material_verification_template_path,
        result.readme_path,
        result.run_commands_path,
        result.manifest_path,
    ):
        assert Path(path_text).exists()
    assert result.preview_path is not None
    assert Path(result.preview_path).exists()
    assert (output_dir / "docs" / "quickstart.md").exists()
    assert (output_dir / "docs" / "acceptance_checklist.md").exists()
    assert (output_dir / "docs" / "clean_demo_workflow.md").exists()


def test_engineering_handoff_manifest_has_sha256_and_safety_flags(tmp_path):
    output_dir = tmp_path / "handoff_manifest"

    result = build_engineering_handoff_package(output_dir=output_dir)
    payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "engineering_handoff_manifest"
    assert payload["status"] == "pass"
    assert payload["requires_engineer_review"] is True
    assert payload["ml_is_advisory_only"] is True
    assert payload["deterministic_checks_required"] is True
    assert payload["ml_ready_for_project_use"] is False
    relative_paths = {file_info["relative_path"] for file_info in payload["files"]}
    assert "input/rectangular_input.json" in relative_paths
    assert "demo/rectangular_clean_demo_input.json" in relative_paths
    assert "previews/input_form_preview.html" in relative_paths
    assert all(len(file_info["sha256"]) == 64 for file_info in payload["files"])


def test_engineering_handoff_package_readme_and_commands_are_scaffold_only(tmp_path):
    output_dir = tmp_path / "handoff_text"

    result = build_engineering_handoff_package(output_dir=output_dir)
    readme = Path(result.readme_path).read_text(encoding="utf-8")
    commands = Path(result.run_commands_path).read_text(encoding="utf-8")

    assert "review scaffold only" in readme
    assert "ml_ready_for_project_use = false" in readme
    assert "python -m sp63_core engineering-workflow" in commands
    assert "python -m sp63_core material-verification-closure" in commands
    forbidden_tokens = ("streamlit", "gradio", "fastapi", "flask", "electron")
    assert all(token not in (readme + commands).lower() for token in forbidden_tokens)


def test_cli_engineering_handoff_package_json(tmp_path, capsys):
    output_dir = tmp_path / "handoff_cli"

    exit_code = main(
        [
            "engineering-handoff-package",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-handoff-package"
    assert payload["status"] == "pass"
    assert payload["package_status"] == "pass"
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["manifest_path"]).exists()
