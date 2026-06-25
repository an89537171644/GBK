import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_portable_package


def test_portable_package_creates_expected_files(tmp_path):
    result = build_portable_package(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.package_status == "pass"
    assert result.script_count == 4
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    for relative_path in (
        "README_PORTABLE_PACKAGE.md",
        "INSTALL_WINDOWS.md",
        "RUN_CLEAN_DEMO.cmd",
        "RUN_PREFLIGHT.cmd",
        "RUN_WORKFLOW.cmd",
        "OPEN_REPORT_INDEX.cmd",
        "input/rectangular_input.json",
        "evidence/external_validation_template.csv",
        "evidence/material_verification_template.csv",
        "docs/quickstart.md",
        "docs/acceptance_checklist.md",
        "portable_manifest.json",
    ):
        assert (tmp_path / relative_path).exists()


def test_portable_package_cmd_files_call_sp63_core(tmp_path):
    build_portable_package(output_dir=tmp_path)

    for path in tmp_path.glob("*.cmd"):
        content = path.read_text(encoding="utf-8")
        if path.name != "OPEN_REPORT_INDEX.cmd":
            assert "python -m sp63_core" in content
        assert "engineer review remain mandatory" in content


def test_portable_package_manifest_has_sha256_and_no_binary_files(tmp_path):
    result = build_portable_package(output_dir=tmp_path)
    payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "portable_package_manifest"
    assert payload["ml_ready_for_project_use"] is False
    assert payload["files"]
    for file_info in payload["files"]:
        assert len(file_info["sha256"]) == 64
        assert not file_info["relative_path"].lower().endswith((".exe", ".dll", ".bin"))


def test_portable_package_docs_exist():
    assert Path("docs/portable_package.md").exists()
    assert Path("docs/user_manual/quickstart.md").exists()


def test_cli_portable_package_json(tmp_path, capsys):
    exit_code = main(["portable-package", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "portable-package"
    assert payload["status"] == "pass"
    assert payload["script_count"] == 4
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "portable_manifest.json").exists()
