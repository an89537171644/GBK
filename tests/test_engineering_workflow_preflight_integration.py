import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import run_engineering_workflow

EXAMPLE_INPUT = Path("docs/reports/examples/rectangular_design_input_example.json")
INVALID_INPUT = Path(
    "docs/reports/examples/form_templates/rectangular_preflight_invalid_input.json"
)


def test_engineering_workflow_with_preflight_creates_reports_and_summary(tmp_path):
    output_dir = tmp_path / "workflow_preflight"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    summary = json.loads((output_dir / "workflow_summary.json").read_text(encoding="utf-8"))
    assert result.preflight_status == "pass"
    assert result.preflight_errors_count == 0
    assert result.preflight_report_json_path == str(output_dir / "input_preflight_report.json")
    assert result.preflight_report_markdown_path == str(output_dir / "input_preflight_report.md")
    assert (output_dir / "input_preflight_report.json").exists()
    assert (output_dir / "input_preflight_report.md").exists()
    assert summary["preflight_status"] == "pass"
    assert summary["preflight_errors_count"] == 0
    assert summary["preflight_warnings_count"] == 0
    assert summary["preflight_report_json_path"] == str(
        output_dir / "input_preflight_report.json"
    )
    assert result.deterministic_report_status == "pass"
    assert result.index_status == "pass"


def test_engineering_workflow_with_preflight_index_links_reports(tmp_path):
    output_dir = tmp_path / "workflow_preflight_index"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert result.index_path == str(output_dir / "index.html")
    assert "input_preflight_report.json" in html
    assert "input_preflight_report.md" in html


def test_engineering_workflow_preflight_fail_stops_deterministic_report(tmp_path):
    output_dir = tmp_path / "workflow_preflight_fail"

    result = run_engineering_workflow(
        input_json_path=INVALID_INPUT,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    summary = json.loads((output_dir / "workflow_summary.json").read_text(encoding="utf-8"))
    assert result.workflow_status == "fail"
    assert result.preflight_status == "fail"
    assert result.preflight_errors_count > 0
    assert result.deterministic_report_status == "skipped"
    assert result.archive_validation_status == "skipped"
    assert result.zip_status == "skipped"
    assert result.index_status == "review_required"
    assert not (output_dir / "deterministic_report").exists()
    assert not (output_dir / "deterministic_report.zip").exists()
    assert summary["workflow_status"] == "fail"
    assert summary["preflight_status"] == "fail"
    assert summary["archive_validation_status"] == "skipped"


def test_engineering_workflow_without_preflight_preserves_old_behavior(tmp_path):
    output_dir = tmp_path / "workflow_without_preflight"

    result = run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    summary = json.loads((output_dir / "workflow_summary.json").read_text(encoding="utf-8"))
    assert result.preflight_status is None
    assert result.preflight_report_json_path is None
    assert result.preflight_report_markdown_path is None
    assert result.deterministic_report_status == "pass"
    assert not (output_dir / "input_preflight_report.json").exists()
    assert summary["preflight_status"] is None


def test_cli_engineering_workflow_with_preflight_and_index_json(tmp_path, capsys):
    output_dir = tmp_path / "workflow_cli_preflight"

    exit_code = main(
        [
            "engineering-workflow",
            "--input-json",
            str(EXAMPLE_INPUT),
            "--output-dir",
            str(output_dir),
            "--with-preflight",
            "--with-index",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-workflow"
    assert payload["preflight_status"] == "pass"
    assert payload["deterministic_report_status"] == "pass"
    assert payload["index_status"] == "pass"
    assert (output_dir / "input_preflight_report.json").exists()
    assert (output_dir / "input_preflight_report.md").exists()
    assert (output_dir / "index.html").exists()


def test_engineering_workflow_preflight_integration_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/engineering_workflow.py").read_text(
        encoding="utf-8"
    )
    index_source = Path("src/sp63_core/workflows/static_report_index.py").read_text(
        encoding="utf-8"
    )

    for protected_import in (
        "sp63_core.checks.bending",
        "sp63_core.checks.shear",
        "sp63_core.checks.cracking",
        "sp63_core.checks.crack_width",
        "sp63_core.checks.deflection",
    ):
        assert protected_import not in source
        assert protected_import not in index_source
