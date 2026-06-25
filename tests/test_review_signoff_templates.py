import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_review_signoff_templates


def test_review_signoff_templates_generate_placeholder_files(tmp_path):
    result = build_review_signoff_templates(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.template_count == 4
    assert result.project_use_allowed is False
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.ml_ready_for_project_use is False
    for path in result.generated_files:
        assert Path(path).exists()


def test_review_signoff_templates_contain_required_placeholder_fields(tmp_path):
    result = build_review_signoff_templates(output_dir=tmp_path)
    for path in result.generated_files:
        if not path.endswith("_template.md"):
            continue
        text = Path(path).read_text(encoding="utf-8")
        for field in (
            "engineer_name_placeholder",
            "review_date_placeholder",
            "organization_placeholder",
            "scope:",
            "reviewed_artifacts:",
            "status:",
            "notes:",
            "signature_placeholder",
        ):
            assert field in text
        assert "<engineer name>" in text
        assert "ml_ready_for_project_use = false" in text


def test_review_signoff_manifest(tmp_path):
    result = build_review_signoff_templates(output_dir=tmp_path)
    payload = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert payload["report_type"] == "review_signoff_templates"
    assert payload["status"] == "pass"
    assert payload["template_count"] == 4
    assert payload["project_use_allowed"] is False


def test_review_signoff_docs_exist():
    assert Path("docs/review_signoff_templates.md").exists()


def test_cli_review_signoff_templates_json(tmp_path, capsys):
    exit_code = main(["review-signoff-templates", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "review-signoff-templates"
    assert payload["status"] == "pass"
    assert payload["template_count"] == 4
    assert (tmp_path / "material_review_signoff_template.md").exists()
