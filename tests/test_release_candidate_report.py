import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_release_candidate_report


def test_release_candidate_report_creates_files(tmp_path):
    result = build_release_candidate_report(output_dir=tmp_path)

    assert result.status in {"pass", "review_required"}
    assert result.release_candidate_status == "review_required"
    assert result.validation_status == "pass"
    assert result.manual_cases_status == "pass"
    assert result.external_validation_status == "pass"
    assert result.protected_files_guard_status in {"pass", "review_required"}
    assert result.user_manual_status == "pass"
    assert result.ml_ready_for_project_use is False
    assert result.requires_engineer_review is True
    assert (tmp_path / "release_candidate_report.json").exists()
    assert (tmp_path / "release_candidate_report.md").exists()
    assert (tmp_path / "README_RELEASE_CANDIDATE.md").exists()


def test_release_candidate_report_contains_known_limitations(tmp_path):
    result = build_release_candidate_report(output_dir=tmp_path)

    payload = json.loads((tmp_path / "release_candidate_report.json").read_text(encoding="utf-8"))
    markdown = (tmp_path / "release_candidate_report.md").read_text(encoding="utf-8")
    assert "not certified" in result.known_limitations
    assert "engineer review required" in result.known_limitations
    assert "ML advisory-only" in result.known_limitations
    assert payload["report_type"] == "release_candidate_report"
    assert payload["ml_ready_for_project_use"] is False
    assert "Known Limitations" in markdown


def test_cli_release_candidate_report_json(tmp_path, capsys):
    output_dir = tmp_path / "release_candidate"

    exit_code = main(
        [
            "release-candidate-report",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-candidate-report"
    assert payload["release_candidate_status"] == "review_required"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "release_candidate_report.json").exists()


def test_cli_release_candidate_report_markdown(tmp_path, capsys):
    output_dir = tmp_path / "release_candidate_markdown"

    exit_code = main(
        [
            "release-candidate-report",
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# Release Candidate Report" in output
    assert "ml_ready_for_project_use = false" in output


def test_release_candidate_report_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/release_candidate.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
