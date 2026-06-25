import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_static_launcher_dashboard


def test_static_launcher_dashboard_generates_files(tmp_path):
    result = build_static_launcher_dashboard(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.command_count >= 4
    assert result.project_use_allowed is False
    assert result.web_server_required is False
    assert result.javascript_calculations_present is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_static_launcher_dashboard_html_has_warnings_and_no_script(tmp_path):
    result = build_static_launcher_dashboard(output_dir=tmp_path)
    html = Path(result.dashboard_html_path).read_text(encoding="utf-8")

    assert "<script" not in html.lower()
    assert "ml_ready_for_project_use = false" in html
    assert "project_use_allowed = false" in html
    assert "python -m sp63_core validate --golden" in html
    assert "clean demo report index" in html
    assert "user manual quickstart" in html


def test_static_launcher_dashboard_json(tmp_path):
    result = build_static_launcher_dashboard(output_dir=tmp_path)
    payload = json.loads(Path(result.dashboard_json_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "static_launcher_dashboard"
    assert payload["status"] == "pass"
    assert payload["web_server_required"] is False
    assert payload["javascript_calculations_present"] is False
    assert payload["ml_ready_for_project_use"] is False


def test_static_launcher_dashboard_docs_exist():
    assert Path("docs/static_launcher_dashboard.md").exists()
    assert Path("docs/ui/engineering_gui_wrapper_contract.md").exists()


def test_cli_static_launcher_dashboard_json(tmp_path, capsys):
    exit_code = main(["static-launcher-dashboard", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "static-launcher-dashboard"
    assert payload["status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "launcher_dashboard.html").exists()
