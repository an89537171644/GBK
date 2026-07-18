import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.dataset import DATASET_VERSION, REQUIRED_REPORT_DATASET_COLUMNS
from sp63_core.workflows import (
    build_static_workflow_report_index,
    run_engineering_workflow,
)

EXAMPLE_INPUT = Path("docs/reports/examples/rectangular_design_input_example.json")
EXTERNAL_FIXTURE = Path("tests/fixtures/external_validation_sample.csv")
MATERIAL_FIXTURE = Path("tests/fixtures/material_verification_sample.csv")


def _dataset_row() -> dict[str, object]:
    row: dict[str, object] = {column: "1" for column in REQUIRED_REPORT_DATASET_COLUMNS}
    row.update(
        {
            "dataset_source": "validated_report_archive",
            "dataset_version": DATASET_VERSION,
            "case_id": "case_001",
            "source_archive_path": "reports/case_001",
            "report_json_path": "reports/case_001/report.json",
            "input_json_path": "reports/case_001/input.json",
            "manifest_path": "reports/case_001/manifest.json",
            "input_sha256": "a" * 64,
            "report_json_sha256": "b" * 64,
            "manifest_sha256": "c" * 64,
            "archive_validation_status": "pass",
            "status_scope": "public",
            "local_axes_id": "case-001-local-axes",
            "moment_axis": "local_z",
            "tension_face": "local_y_min",
            "load_duration": "short",
            "completeness_status": "incomplete",
            "evidence_status": "needs_engineer_review",
            "project_use_status": "prohibited",
            "project_use": False,
            "b": 300,
            "h": 500,
            "cover": 32,
            "concrete_class": "B25",
            "longitudinal_rebar_class": "A500",
            "stirrup_rebar_class": "A240",
            "M": 150_000_000,
            "Q": 80_000,
            "bending_status": "outside_applicability",
            "strength_status": "outside_applicability",
            "serviceability_status": "pass",
            "overall_status": "outside_applicability",
            "warnings_count": 0,
            "requires_engineer_review": True,
            "ml_is_advisory_only": True,
            "deterministic_checks_required": True,
            "external_validation_status": "not_provided",
            "material_verification_status": "not_provided",
        }
    )
    return row


def _write_jsonl_dataset(path: Path) -> Path:
    path.write_text(json.dumps(_dataset_row(), ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def test_static_workflow_report_index_for_deterministic_workflow(tmp_path):
    output_dir = tmp_path / "workflow"
    run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    result = build_static_workflow_report_index(workflow_dir=output_dir)

    index_path = output_dir / "index.html"
    html = index_path.read_text(encoding="utf-8")
    assert result.status == "pass"
    assert result.index_status == "pass"
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert "deterministic_report/report.html" in result.linked_files
    assert "workflow_summary.md" in result.linked_files
    assert "deterministic_report.zip" in result.linked_files
    assert result.missing_expected_files == ()
    assert "This static index does not certify the design" in html
    assert "deterministic_report/report.html" in html
    assert "workflow_summary.md" in html
    assert "deterministic_report.zip" in html
    assert "ml_ready_for_project_use" in html
    assert "<script" not in html.lower()
    assert "<form" not in html.lower()
    assert "Approve design" not in html


def test_static_workflow_report_index_warns_when_ml_readiness_is_optional(tmp_path):
    output_dir = tmp_path / "workflow"
    run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    result = build_static_workflow_report_index(workflow_dir=output_dir)

    assert result.status == "pass"
    assert (
        "ML readiness outputs were not found; deterministic-only workflow index generated."
        in result.warnings
    )


def test_static_workflow_report_index_links_optional_ml_readiness(tmp_path):
    dataset = _write_jsonl_dataset(tmp_path / "dataset.jsonl")
    output_dir = tmp_path / "workflow_ml"
    run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        include_ml_readiness=True,
        dataset_path=dataset,
        external_validation_csv=EXTERNAL_FIXTURE,
        material_verification_csv=MATERIAL_FIXTURE,
    )

    result = build_static_workflow_report_index(workflow_dir=output_dir)

    assert result.status == "pass"
    assert "ml_readiness/engineering_ml_readiness.md" in result.linked_files
    assert "ml_readiness/engineering_ml_readiness.json" in result.linked_files


def test_static_workflow_report_index_missing_critical_file_is_review_required(tmp_path):
    workflow_dir = tmp_path / "incomplete_workflow"
    workflow_dir.mkdir()
    (workflow_dir / "workflow_summary.json").write_text(
        json.dumps({"workflow_status": "review_required"}),
        encoding="utf-8",
    )

    result = build_static_workflow_report_index(workflow_dir=workflow_dir)

    assert result.status == "review_required"
    assert "deterministic_report/report.html" in result.missing_expected_files
    assert "Critical workflow files are missing; static index requires engineer review." in (
        result.warnings
    )


def test_cli_engineering_report_index_json(tmp_path, capsys):
    output_dir = tmp_path / "workflow"
    run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    exit_code = main(["engineering-report-index", "--workflow-dir", str(output_dir), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-report-index"
    assert payload["status"] == "pass"
    assert payload["index_status"] == "pass"
    assert payload["ml_ready_for_project_use"] is False
    assert (output_dir / "index.html").exists()


def test_cli_engineering_report_index_custom_output_json(tmp_path, capsys):
    output_dir = tmp_path / "workflow"
    custom_output = output_dir / "index_custom.html"
    run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)

    exit_code = main(
        [
            "engineering-report-index",
            "--workflow-dir",
            str(output_dir),
            "--output",
            str(custom_output),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["output_path"] == str(custom_output)
    assert custom_output.exists()


def test_cli_engineering_report_index_open_in_browser_does_not_fail(
    tmp_path,
    capsys,
    monkeypatch,
):
    output_dir = tmp_path / "workflow"
    run_engineering_workflow(input_json_path=EXAMPLE_INPUT, output_dir=output_dir)
    monkeypatch.setattr("sp63_core.cli.webbrowser.open", lambda _url: False)

    exit_code = main(
        [
            "engineering-report-index",
            "--workflow-dir",
            str(output_dir),
            "--open-in-browser",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["open_browser_status"] == "not_opened"
    assert "open-in-browser requested but browser did not open" in payload["warnings"]


def test_engineering_workflow_with_index_creates_static_index(tmp_path):
    output_dir = tmp_path / "workflow_with_index"

    result = run_engineering_workflow(
        input_json_path=EXAMPLE_INPUT,
        output_dir=output_dir,
        with_index=True,
    )

    assert result.index_status == "pass"
    assert result.index_path == str(output_dir / "index.html")
    assert (output_dir / "index.html").exists()
    summary = json.loads((output_dir / "workflow_summary.json").read_text(encoding="utf-8"))
    assert summary["index_status"] == "pass"
    assert summary["index_path"] == str(output_dir / "index.html")
    assert "index.html" in (output_dir / "README_WORKFLOW.md").read_text(encoding="utf-8")


def test_cli_engineering_workflow_with_index_json(tmp_path, capsys):
    output_dir = tmp_path / "workflow_cli_with_index"

    exit_code = main(
        [
            "engineering-workflow",
            "--input-json",
            str(EXAMPLE_INPUT),
            "--output-dir",
            str(output_dir),
            "--with-index",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-workflow"
    assert payload["index_status"] == "pass"
    assert payload["index_path"] == str(output_dir / "index.html")
    assert (output_dir / "index.html").exists()


def test_static_workflow_report_index_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/static_report_index.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
