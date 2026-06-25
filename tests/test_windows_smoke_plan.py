import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_windows_smoke_plan


def test_windows_smoke_plan_generates_expected_files(tmp_path):
    result = build_windows_smoke_plan(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.command_count >= 4
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_windows_smoke_plan_content_is_manual_only(tmp_path):
    build_windows_smoke_plan(output_dir=tmp_path)
    plan = (tmp_path / "WINDOWS_SMOKE_PLAN.md").read_text(encoding="utf-8")
    ps1 = (tmp_path / "WINDOWS_COMMANDS.ps1").read_text(encoding="utf-8")
    cmd = (tmp_path / "WINDOWS_COMMANDS.cmd").read_text(encoding="utf-8")

    assert "validate --golden" in plan
    assert "clean-demo-workflow" in plan
    assert "protected-files-check" in ps1
    assert "release-bundle" in cmd
    assert "Do not commit generated" in ps1
    assert "project_use_allowed = false" in plan


def test_windows_smoke_manifest(tmp_path):
    build_windows_smoke_plan(output_dir=tmp_path)
    payload = json.loads((tmp_path / "windows_smoke_manifest.json").read_text(encoding="utf-8"))

    assert payload["report_type"] == "windows_smoke_plan"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert payload["command_count"] >= 4


def test_windows_smoke_docs_exist():
    assert Path("docs/windows_clean_machine_smoke.md").exists()
    assert Path("docs/portable_package.md").exists()
    assert Path("docs/user_manual/quickstart.md").exists()


def test_cli_windows_smoke_plan_json(tmp_path, capsys):
    exit_code = main(["windows-smoke-plan", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "windows-smoke-plan"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "WINDOWS_COMMANDS.ps1").exists()
