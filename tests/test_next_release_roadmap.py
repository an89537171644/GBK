import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_next_release_roadmap


def test_next_release_roadmap_builds_sections(tmp_path):
    result = build_next_release_roadmap(output_dir=tmp_path)

    assert result.status == "review_required"
    assert result.roadmap_status == "review_required"
    assert result.section_count >= 8
    assert result.review_required_count >= 1
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_next_release_roadmap_contains_required_sections(tmp_path):
    result = build_next_release_roadmap(output_dir=tmp_path)
    sections = {section["section_id"]: section for section in result.sections}

    for section_id in (
        "v09_internal_review",
        "v09_user_trial",
        "v10_engineering_release",
        "gui_launcher",
        "material_verification",
        "external_validation",
        "ml_advisory_maturity",
        "installer_packaging",
    ):
        assert section_id in sections
    assert sections["ml_advisory_maturity"]["status"] == "advisory_only"


def test_next_release_roadmap_json_markdown_readme(tmp_path):
    result = build_next_release_roadmap(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    readme = Path(result.readme_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "next_release_roadmap"
    assert payload["project_use_allowed"] is False
    assert "Next Release Roadmap" in markdown
    assert "ml_ready_for_project_use = false" in markdown
    assert "README Next Release Roadmap" in readme


def test_next_release_roadmap_docs_exist():
    assert Path("docs/next_release_roadmap.md").exists()
    assert Path("docs/v10_gap_report.md").exists()


def test_cli_next_release_roadmap_json(tmp_path, capsys):
    exit_code = main(["next-release-roadmap", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "next-release-roadmap"
    assert payload["status"] == "review_required"
    assert payload["section_count"] >= 8
    assert payload["project_use_allowed"] is False
