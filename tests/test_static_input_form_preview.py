import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_static_input_form_preview


def test_static_input_form_preview_creates_files(tmp_path):
    result = build_static_input_form_preview(output_dir=tmp_path)

    assert result.status == "pass"
    assert result.preview_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert result.schema_field_count > 0
    assert (tmp_path / "input_form_preview.html").exists()
    assert (tmp_path / "input_form_preview.json").exists()
    assert (tmp_path / "README_INPUT_FORM_PREVIEW.md").exists()


def test_static_input_form_preview_html_contains_required_content(tmp_path):
    build_static_input_form_preview(output_dir=tmp_path)
    html_text = (tmp_path / "input_form_preview.html").read_text(encoding="utf-8")

    assert "This static preview does not perform design calculations" in html_text
    assert "geometry" in html_text
    assert "materials" in html_text
    assert "loads" in html_text
    assert "<code>b</code>" in html_text
    assert "<code>concrete_class</code>" in html_text
    assert "<code>M</code>" in html_text
    assert "ml_ready_for_project_use = false" in html_text
    assert "Design calculations are executed only through the deterministic workflow" in html_text
    assert "Approve design" not in html_text
    assert "<script" not in html_text.lower()


def test_static_input_form_preview_json_metadata(tmp_path):
    result = build_static_input_form_preview(output_dir=tmp_path)
    payload = json.loads((tmp_path / "input_form_preview.json").read_text(encoding="utf-8"))

    assert payload["preview_type"] == "static_input_form_preview"
    assert payload["status"] == "pass"
    assert payload["schema_field_count"] == result.schema_field_count
    assert payload["ml_ready_for_project_use"] is False
    assert "input_form_preview.html" in payload["generated_files"]


def test_cli_input_form_preview_json(tmp_path, capsys):
    exit_code = main(["input-form-preview", "--output-dir", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "input-form-preview"
    assert payload["status"] == "pass"
    assert payload["preview_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (tmp_path / "input_form_preview.html").exists()


def test_cli_input_form_preview_markdown(tmp_path, capsys):
    exit_code = main(["input-form-preview", "--output-dir", str(tmp_path), "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering Input Form Preview" in output
    assert "ml_ready_for_project_use = false" in output
    assert (tmp_path / "README_INPUT_FORM_PREVIEW.md").exists()


def test_cli_input_form_preview_no_output_files(tmp_path, capsys):
    exit_code = main(
        [
            "input-form-preview",
            "--output-dir",
            str(tmp_path),
            "--no-output-files",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["output_dir"] is None
    assert not (tmp_path / "input_form_preview.html").exists()


def test_static_input_form_preview_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/static_input_form_preview.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
