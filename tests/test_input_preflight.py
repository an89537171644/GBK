import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import run_input_preflight

EXAMPLE_INPUT = Path("docs/reports/examples/rectangular_design_input_example.json")
TEMPLATE_DIR = Path("docs/reports/examples/form_templates")


def test_input_preflight_valid_example_passes():
    result = run_input_preflight(EXAMPLE_INPUT)

    assert result.status == "pass"
    assert result.preflight_status == "pass"
    assert result.error_count == 0
    assert result.warning_count == 0
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert "b" in result.checked_fields


def test_input_preflight_review_required_when_service_moment_exceeds_design_moment():
    result = run_input_preflight(TEMPLATE_DIR / "rectangular_preflight_review_input.json")

    assert result.status == "review_required"
    assert result.error_count == 0
    assert result.warning_count == 1
    assert "Mser is greater than M." in result.warnings


def test_input_preflight_rejects_invalid_example():
    result = run_input_preflight(TEMPLATE_DIR / "rectangular_preflight_invalid_input.json")

    assert result.status == "fail"
    assert result.error_count > 0
    assert "unknown_demo_field" in result.unknown_fields
    assert "ml_ready_for_project_use" in result.unknown_fields
    assert any(issue.issue_id == "ml_ready_not_user_settable" for issue in result.issues)
    assert any(issue.issue_id == "unknown_concrete_class" for issue in result.issues)


def test_input_preflight_rejects_missing_required_fields(tmp_path):
    input_path = tmp_path / "missing_required.json"
    input_path.write_text(
        json.dumps(
            {
                "b": 300,
                "h": 500,
                "cover": 32,
                "stirrup_diameter_for_geometry": 8,
                "concrete_class": "B25",
            }
        ),
        encoding="utf-8",
    )

    result = run_input_preflight(input_path)

    assert result.status == "fail"
    assert "M" in result.missing_required_fields
    assert "Q" in result.missing_required_fields
    assert "longitudinal_rebar_class" in result.missing_required_fields
    assert "stirrup_rebar_class" in result.missing_required_fields


def test_input_preflight_rejects_invalid_json_and_non_object(tmp_path):
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    list_path = tmp_path / "list.json"
    list_path.write_text("[1, 2, 3]", encoding="utf-8")

    invalid_result = run_input_preflight(invalid_path)
    list_result = run_input_preflight(list_path)

    assert invalid_result.status == "fail"
    assert any(issue.issue_id == "input_json_invalid" for issue in invalid_result.issues)
    assert list_result.status == "fail"
    assert any(issue.issue_id == "input_json_not_object" for issue in list_result.issues)


def test_input_preflight_requires_dataset_for_ml_readiness(tmp_path):
    input_path = tmp_path / "ml_missing_dataset.json"
    data = json.loads(EXAMPLE_INPUT.read_text(encoding="utf-8"))
    data["include_ml_readiness"] = True
    input_path.write_text(json.dumps(data), encoding="utf-8")

    result = run_input_preflight(input_path)

    assert result.status == "fail"
    assert any(issue.issue_id == "dataset_required_for_ml_readiness" for issue in result.issues)


def test_input_preflight_rejects_missing_optional_csv_path(tmp_path):
    input_path = tmp_path / "missing_csv.json"
    data = json.loads(EXAMPLE_INPUT.read_text(encoding="utf-8"))
    data["external_validation_csv"] = "missing_external_validation.csv"
    input_path.write_text(json.dumps(data), encoding="utf-8")

    result = run_input_preflight(input_path)

    assert result.status == "fail"
    assert any(issue.issue_id == "path_field_missing" for issue in result.issues)


def test_input_preflight_writes_output_files(tmp_path):
    result = run_input_preflight(EXAMPLE_INPUT, output_dir=tmp_path)

    json_path = tmp_path / "input_preflight_report.json"
    markdown_path = tmp_path / "input_preflight_report.md"
    assert json_path.exists()
    assert markdown_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["report_type"] == "input_preflight_report"
    assert payload["status"] == result.status
    assert payload["ml_ready_for_project_use"] is False
    assert "Input JSON Preflight Report" in markdown_path.read_text(encoding="utf-8")


def test_cli_input_preflight_json(tmp_path, capsys):
    output_dir = tmp_path / "preflight"

    exit_code = main(
        [
            "input-preflight",
            "--input-json",
            str(EXAMPLE_INPUT),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "input-preflight"
    assert payload["status"] == "pass"
    assert payload["preflight_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "input_preflight_report.json").exists()
    assert (output_dir / "input_preflight_report.md").exists()


def test_cli_input_preflight_markdown(tmp_path, capsys):
    output_dir = tmp_path / "preflight_markdown"

    exit_code = main(
        [
            "input-preflight",
            "--input-json",
            str(TEMPLATE_DIR / "rectangular_serviceability_input_template.json"),
            "--output-dir",
            str(output_dir),
            "--markdown",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Input JSON Preflight Report" in output
    assert "ml_ready_for_project_use = false" in output
    assert (output_dir / "input_preflight_report.md").exists()


def test_input_preflight_templates_are_valid_json_and_anonymized():
    template_paths = (
        TEMPLATE_DIR / "rectangular_preflight_invalid_input.json",
        TEMPLATE_DIR / "rectangular_preflight_review_input.json",
    )

    for template_path in template_paths:
        payload = json.loads(template_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        assert "passport" not in template_path.read_text(encoding="utf-8").lower()
        assert "snils" not in template_path.read_text(encoding="utf-8").lower()


def test_input_preflight_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/input_preflight.py").read_text(encoding="utf-8")

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
    assert "sp63_core.design" not in source
