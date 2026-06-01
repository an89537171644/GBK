import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import build_input_form_schema

TEMPLATE_DIR = Path("docs/reports/examples/form_templates")
REQUIRED_DESIGN_FIELDS = {
    "b",
    "h",
    "cover",
    "stirrup_diameter_for_geometry",
    "concrete_class",
    "longitudinal_rebar_class",
    "stirrup_rebar_class",
    "M",
    "Q",
}


def _field_names(result) -> set[str]:
    return {
        field["name"]
        for group in result.json_data["groups"]
        for field in group["fields"]
    }


def _group(result, name: str) -> dict:
    return next(group for group in result.json_data["groups"] if group["group"] == name)


def test_input_form_schema_builder_returns_pass():
    result = build_input_form_schema()

    assert result.status == "pass"
    assert result.schema_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert result.errors == ()
    assert result.field_count > 0
    assert result.validation_rules_count > 0


def test_input_form_schema_contains_expected_field_groups():
    result = build_input_form_schema()

    assert {group["group"] for group in result.json_data["groups"]} >= {
        "geometry",
        "materials",
        "loads",
        "checks",
        "workflow",
        "ml_readiness",
    }
    assert {"b", "h", "cover", "span"} <= _field_names(result)
    assert {
        "concrete_class",
        "longitudinal_rebar_class",
        "stirrup_rebar_class",
    } <= _field_names(result)
    assert {"M", "Q", "Mser"} <= _field_names(result)
    assert {"check_cracks", "check_crack_width", "check_deflection"} <= _field_names(result)
    assert {"output_dir", "create_zip", "with_index", "include_ml_readiness"} <= _field_names(
        result
    )
    assert {"dataset_path", "external_validation_csv", "material_verification_csv"} <= (
        _field_names(result)
    )


def test_input_form_schema_fields_have_metadata():
    result = build_input_form_schema()

    for group in result.json_data["groups"]:
        for field in group["fields"]:
            assert field["name"]
            assert field["label"]
            assert field["label_ru"]
            assert field["type"]
            assert "required" in field
            assert "engineering_hint" in field
            assert "validation_message" in field


def test_input_form_schema_validation_rules_and_warnings():
    result = build_input_form_schema()
    rule_ids = {rule["rule_id"] for rule in result.json_data["validation_rules"]}

    assert "positive_dimensions" in rule_ids
    assert "material_classes_exist" in rule_ids
    assert "dataset_required_for_ml_readiness" in rule_ids
    assert "ml_ready_not_user_settable" in rule_ids
    assert any("future UI/input forms only" in warning for warning in result.warnings)
    assert result.json_data["ml_ready_for_project_use"] is False
    assert "ml_ready_for_project_use" not in _field_names(result)


def test_input_form_schema_writes_output_files(tmp_path):
    result = build_input_form_schema(output_dir=tmp_path)

    json_path = tmp_path / "input_form_schema.json"
    markdown_path = tmp_path / "input_form_schema.md"
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema_type"] == "engineering_input_form_schema"
    assert payload["field_count"] == result.field_count
    assert payload["ml_ready_for_project_use"] is False
    assert "Engineering Input Form Schema" in markdown_path.read_text(encoding="utf-8")


def test_cli_input_form_schema_json(tmp_path, capsys):
    output_dir = tmp_path / "schema"

    exit_code = main(["input-form-schema", "--output-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "input-form-schema"
    assert payload["status"] == "pass"
    assert payload["schema_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "input_form_schema.json").exists()
    assert (output_dir / "input_form_schema.md").exists()


def test_cli_input_form_schema_markdown(tmp_path, capsys):
    output_dir = tmp_path / "schema_markdown"

    exit_code = main(["input-form-schema", "--output-dir", str(output_dir), "--markdown"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Engineering Input Form Schema" in output
    assert "ml_ready_for_project_use = false" in output
    assert (output_dir / "input_form_schema.json").exists()
    assert (output_dir / "input_form_schema.md").exists()


def test_cli_input_form_schema_no_output_files(tmp_path, capsys):
    output_dir = tmp_path / "schema_no_files"

    exit_code = main(
        ["input-form-schema", "--output-dir", str(output_dir), "--no-output-files", "--json"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["output_dir"] is None
    assert not output_dir.exists()


def test_input_form_schema_templates_are_valid_json_and_anonymized():
    template_paths = (
        TEMPLATE_DIR / "rectangular_minimal_input_template.json",
        TEMPLATE_DIR / "rectangular_serviceability_input_template.json",
        TEMPLATE_DIR / "rectangular_ml_readiness_workflow_template.json",
    )

    for template_path in template_paths:
        payload = json.loads(template_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert "personal" not in template_path.read_text(encoding="utf-8").lower()
        assert "grant" not in template_path.read_text(encoding="utf-8").lower()
        assert "ml_ready_for_project_use" not in payload

    minimal = json.loads(template_paths[0].read_text(encoding="utf-8"))
    serviceability = json.loads(template_paths[1].read_text(encoding="utf-8"))
    workflow = json.loads(template_paths[2].read_text(encoding="utf-8"))
    assert set(minimal) >= REQUIRED_DESIGN_FIELDS
    assert set(serviceability) >= REQUIRED_DESIGN_FIELDS
    assert {"check_cracks", "check_crack_width", "check_deflection", "span"} <= set(
        serviceability
    )
    assert {"output_dir", "with_index", "include_ml_readiness", "dataset_path"} <= set(workflow)


def test_input_form_schema_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/input_form_schema.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
