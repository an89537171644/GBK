import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_release_acceptance_checklist


def test_release_acceptance_checklist_builds_review_required_items(tmp_path):
    result = build_release_acceptance_checklist(output_dir=tmp_path)

    assert result.status == "review_required"
    assert result.checklist_status == "review_required"
    assert result.item_count >= 10
    assert result.machine_pass_count >= 1
    assert result.manual_signoff_required_count >= 1
    assert result.review_required_count >= 1
    assert result.failed_count == 0
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_release_acceptance_checklist_contains_required_items(tmp_path):
    result = build_release_acceptance_checklist(output_dir=tmp_path)
    items = {item["item_id"]: item for item in result.items}

    for item_id in (
        "validate_golden",
        "manual_cases",
        "external_validation_sample",
        "materials_engineer_review",
        "protected_files_guard",
        "docs_audit",
        "clean_demo",
        "release_bundle",
        "user_manual",
        "known_limitations_reviewed",
        "ml_ready_false",
        "engineer_signed_review",
    ):
        assert item_id in items
    assert items["engineer_signed_review"]["manual_signoff_required"] is True


def test_release_acceptance_checklist_json_and_markdown(tmp_path):
    result = build_release_acceptance_checklist(output_dir=tmp_path)
    payload = json.loads(Path(result.summary_json_path).read_text(encoding="utf-8"))
    markdown = Path(result.summary_markdown_path).read_text(encoding="utf-8")

    assert payload["report_type"] == "release_acceptance_checklist"
    assert payload["project_use_allowed"] is False
    assert "Release Acceptance Checklist" in markdown
    assert "ml_ready_for_project_use = false" in markdown


def test_release_acceptance_checklist_docs_exist():
    assert Path("docs/release_acceptance_checklist.md").exists()


def test_cli_release_acceptance_checklist_json(tmp_path, capsys):
    exit_code = main(["release-acceptance-checklist", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "release-acceptance-checklist"
    assert payload["status"] == "review_required"
    assert payload["project_use_allowed"] is False
    assert (tmp_path / "release_acceptance_checklist.json").exists()
