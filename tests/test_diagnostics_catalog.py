import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_diagnostics_catalog

REQUIRED_CODES = {
    "missing_required_field",
    "invalid_geometry",
    "cover_greater_or_equal_h",
    "unknown_material_class",
    "material_catalog_review_required",
    "negative_load",
    "mser_greater_than_m",
    "archive_validation_fail",
    "zip_missing",
    "manifest_missing",
    "checksum_mismatch",
    "ml_readiness_incomplete",
    "ml_project_use_forbidden",
    "generated_report_missing",
    "preflight_fail",
    "deterministic_report_fail",
    "engineer_review_required",
}

REQUIRED_CATEGORIES = {
    "input_preflight",
    "geometry",
    "materials",
    "loads",
    "workflow",
    "archive",
    "zip",
    "ml_readiness",
    "protected_files",
    "release_candidate",
}


def test_diagnostics_catalog_contains_required_diagnostics():
    result = build_diagnostics_catalog()
    diagnostics = result.json_data["diagnostics"]
    codes = {item["code"] for item in diagnostics}

    assert result.status == "pass"
    assert result.catalog_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert REQUIRED_CODES.issubset(codes)


def test_diagnostics_catalog_has_required_categories_and_messages():
    result = build_diagnostics_catalog()

    assert REQUIRED_CATEGORIES.issubset(set(result.categories))
    for item in result.json_data["diagnostics"]:
        assert item["severity"] in {"info", "warning", "error"}
        assert item["title_en"]
        assert item["title_ru"]
        assert item["message_en"]
        assert item["message_ru"]
        assert item["recommended_action_en"]
        assert item["recommended_action_ru"]
        assert item["related_command"]


def test_diagnostics_catalog_output_dir_writes_json_and_markdown(tmp_path):
    result = build_diagnostics_catalog(output_dir=tmp_path)

    json_path = tmp_path / "diagnostics_catalog.json"
    markdown_path = tmp_path / "diagnostics_catalog.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert result.status == "pass"
    assert json_path.exists()
    assert markdown_path.exists()
    assert payload["report_type"] == "diagnostics_catalog"
    assert payload["diagnostics_count"] >= len(REQUIRED_CODES)
    assert "Diagnostics Catalog" in markdown
    assert "engineer review" in markdown.lower()


def test_cli_diagnostics_catalog_json(tmp_path, capsys):
    output_dir = tmp_path / "diagnostics"

    exit_code = main(
        [
            "diagnostics-catalog",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "diagnostics-catalog"
    assert payload["status"] == "pass"
    assert payload["diagnostics_count"] >= len(REQUIRED_CODES)
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "diagnostics_catalog.json").exists()
    assert (output_dir / "diagnostics_catalog.md").exists()


def test_cli_diagnostics_catalog_markdown(capsys):
    exit_code = main(["diagnostics-catalog", "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "# Diagnostics Catalog" in output
    assert "missing_required_field" in output
    assert "ml_ready_for_project_use = false" in output


def test_diagnostics_catalog_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/diagnostics_catalog.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
