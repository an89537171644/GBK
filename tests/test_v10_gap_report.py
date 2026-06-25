import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_v10_gap_report


def test_v10_gap_report_builds_review_required_report(tmp_path):
    result = build_v10_gap_report(output_dir=tmp_path)

    assert result.status == "review_required"
    assert result.report_status == "review_required"
    assert result.ready_for_v09_internal_review is True
    assert result.ready_for_v10 is False
    assert result.remaining_steps_estimate >= 6
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert Path(result.summary_json_path).exists()
    assert Path(result.summary_markdown_path).exists()


def test_v10_gap_report_contains_required_gaps(tmp_path):
    result = build_v10_gap_report(output_dir=tmp_path)
    areas = {blocker["area"] for blocker in result.blockers}

    assert "material verification" in areas
    assert "external validation" in areas
    assert "GUI/launcher" in areas
    assert "packaging/installer" in areas
    assert "ML production" in areas
    assert "documentation" in areas


def test_v10_gap_report_json_and_markdown(tmp_path):
    result = build_v10_gap_report(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "v10_gap_report"
    assert payload["ready_for_v10"] is False
    assert "v1.0 Gap And Risk Report" in markdown
    assert "ml_ready_for_project_use = false" in markdown


def test_v10_gap_report_docs_exist():
    assert Path("docs/v10_gap_report.md").exists()
    assert Path("docs/known_limitations_v0_9.md").exists()


def test_cli_v10_gap_report_json(tmp_path, capsys):
    exit_code = main(["v10-gap-report", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "v10-gap-report"
    assert payload["status"] == "review_required"
    assert payload["ready_for_v10"] is False
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "v10_gap_report.json").exists()


def test_cli_v10_gap_report_markdown(tmp_path, capsys):
    exit_code = main(["v10-gap-report", "--output-dir", str(tmp_path), "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "v1.0 Gap And Risk Report" in output
    assert "ready_for_v10: `False`" in output
