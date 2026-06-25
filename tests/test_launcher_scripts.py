import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_launcher_scripts_package


def test_launcher_scripts_package_creates_cmd_and_sh_scripts(tmp_path):
    output_dir = tmp_path / "launchers"

    result = build_launcher_scripts_package(output_dir=output_dir)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.script_count == 8
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    for filename in (
        "run_clean_demo_workflow.cmd",
        "run_clean_demo_workflow.sh",
        "run_engineering_workflow.cmd",
        "run_engineering_workflow.sh",
        "run_engineering_workflow_batch.cmd",
        "run_engineering_workflow_batch.sh",
        "open_clean_demo_index.cmd",
        "open_clean_demo_index.sh",
    ):
        assert (output_dir / filename).exists()


def test_launcher_scripts_manifest_has_checksums(tmp_path):
    output_dir = tmp_path / "launchers_manifest"

    result = build_launcher_scripts_package(output_dir=output_dir)
    payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "launcher_scripts_manifest"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    relative_paths = {file_info["relative_path"] for file_info in payload["files"]}
    assert "run_clean_demo_workflow.cmd" in relative_paths
    assert "run_engineering_workflow.sh" in relative_paths
    assert "README_LAUNCHER_SCRIPTS.md" in relative_paths
    assert all(len(file_info["sha256"]) == 64 for file_info in payload["files"])


def test_launcher_scripts_are_cli_wrappers_only(tmp_path):
    output_dir = tmp_path / "launchers_text"

    result = build_launcher_scripts_package(output_dir=output_dir)
    combined_text = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in result.generated_files
        if Path(path).suffix in {".cmd", ".sh"}
    )

    assert "python -m sp63_core" in combined_text
    assert "deterministic checks and engineer review remain mandatory" in combined_text
    forbidden_tokens = (
        "streamlit",
        "gradio",
        "fastapi",
        "flask",
        "electron",
        "pyside",
        "pyqt",
        "tkinter",
        "torch",
        "tensorflow",
        "keras",
    )
    assert all(token not in combined_text for token in forbidden_tokens)


def test_cli_launcher_scripts_json(tmp_path, capsys):
    output_dir = tmp_path / "launchers_cli"

    exit_code = main(
        [
            "launcher-scripts",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "launcher-scripts"
    assert payload["status"] == "pass"
    assert payload["script_count"] == 8
    assert payload["requires_engineer_review"] is True
    assert payload["ml_ready_for_project_use"] is False
    assert Path(payload["manifest_path"]).exists()
