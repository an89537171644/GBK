import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v09_freeze_report


def test_v09_freeze_report_builds_review_gate(tmp_path):
    result = build_v09_freeze_report(output_dir=tmp_path, version="0.9.0-rc1")

    assert result.status in {"pass", "review_required"}
    assert result.freeze_status == result.status
    assert result.version == "0.9.0-rc1"
    assert result.critical_failed_count == 0
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert Path(result.summary_json_path).exists()
    assert Path(result.summary_markdown_path).exists()
    assert Path(result.readme_path).exists()


def test_v09_freeze_report_contains_required_items(tmp_path):
    result = build_v09_freeze_report(output_dir=tmp_path)
    items = {item["name"]: item for item in result.freeze_items}

    for name in (
        "protected-files-check",
        "docs-audit",
        "user-manual-index",
        "release-notes",
        "release-manifest",
        "release-bundle",
        "clean-demo-verify",
        "traceability-matrix",
        "v10-gap-report",
        "v09-final-audit",
    ):
        assert name in items
    assert items["protected-files-check"]["status"] == "pass"
    assert items["v10-gap-report"]["status"] == "review_required"


def test_v09_freeze_report_json_markdown_and_readme(tmp_path):
    result = build_v09_freeze_report(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    readme = Path(result.readme_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "v09_freeze_report"
    assert payload["project_use_allowed"] is False
    assert "v0.9 Freeze Report" in markdown
    assert "ml_ready_for_project_use = false" in markdown
    assert "README V09 Freeze" in readme


def test_v09_freeze_report_docs_exist():
    assert Path("docs/v09_freeze_report.md").exists()


def test_cli_v09_freeze_report_json(tmp_path, capsys):
    exit_code = main(
        [
            "v09-freeze-report",
            "--output-dir",
            str(tmp_path),
            "--version",
            "0.9.0-rc1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v09-freeze-report"
    assert payload["status"] in {"pass", "review_required"}
    assert payload["critical_failed_count"] == 0
    assert payload["project_use_allowed"] is False
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "v09_freeze_report.json").exists()


def test_cli_v09_freeze_report_markdown(tmp_path, capsys):
    exit_code = main(["v09-freeze-report", "--output-dir", str(tmp_path), "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "v0.9 Freeze Report" in output
    assert "project_use_allowed: `False`" in output
