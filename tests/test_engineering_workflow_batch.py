import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.workflows import run_engineering_workflow_batch

FORM_TEMPLATES = Path("docs/reports/examples/form_templates")


def test_engineering_workflow_batch_runs_form_templates(tmp_path):
    output_dir = tmp_path / "batch"

    result = run_engineering_workflow_batch(
        input_dir=FORM_TEMPLATES,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    expected_case_count = len(tuple(FORM_TEMPLATES.glob("*.json")))
    assert result.case_count == expected_case_count
    assert result.batch_status == "fail"
    assert result.failed_count >= 1
    assert result.review_required_count >= 1
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.ml_ready_for_project_use is False
    assert (output_dir / "batch_workflow_summary.json").exists()
    assert (output_dir / "batch_workflow_summary.md").exists()
    assert (output_dir / "batch_index.html").exists()
    assert (output_dir / "README_BATCH_WORKFLOW.md").exists()
    assert (output_dir / "case_0001").exists()


def test_engineering_workflow_batch_summary_contains_case_statuses(tmp_path):
    output_dir = tmp_path / "batch_summary"

    run_engineering_workflow_batch(
        input_dir=FORM_TEMPLATES,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    payload = json.loads((output_dir / "batch_workflow_summary.json").read_text(encoding="utf-8"))
    assert payload["report_type"] == "batch_engineering_workflow_summary"
    assert payload["case_count"] == len(payload["case_results"])
    assert any(case["preflight_status"] == "fail" for case in payload["case_results"])
    assert any(
        case["deterministic_report_status"] == "pass" for case in payload["case_results"]
    )
    assert payload["failed_count"] >= 1


def test_engineering_workflow_batch_index_links_case_indexes(tmp_path):
    output_dir = tmp_path / "batch_index"

    result = run_engineering_workflow_batch(
        input_dir=FORM_TEMPLATES,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    html = (output_dir / "batch_index.html").read_text(encoding="utf-8")
    assert result.batch_index_path == str(output_dir / "batch_index.html")
    assert "case_0001" in html
    assert "case report" in html
    assert "ml_ready_for_project_use" in html
    assert "<script" not in html.lower()
    assert "Approve design" not in html


def test_engineering_workflow_batch_invalid_case_does_not_break_batch(tmp_path):
    output_dir = tmp_path / "batch_invalid_case"

    result = run_engineering_workflow_batch(
        input_dir=FORM_TEMPLATES,
        output_dir=output_dir,
        with_preflight=True,
        with_index=True,
    )

    failed_cases = [
        case for case in result.case_results if case["workflow_status"] == "fail"
    ]
    assert failed_cases
    assert result.case_count == len(tuple(FORM_TEMPLATES.glob("*.json")))
    assert (output_dir / "batch_workflow_summary.json").exists()


def test_cli_engineering_workflow_batch_json(tmp_path, capsys):
    output_dir = tmp_path / "batch_cli"

    exit_code = main(
        [
            "engineering-workflow-batch",
            "--input-dir",
            str(FORM_TEMPLATES),
            "--output-dir",
            str(output_dir),
            "--with-preflight",
            "--with-index",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["command"] == "engineering-workflow-batch"
    assert payload["batch_status"] == "fail"
    assert payload["case_count"] == len(tuple(FORM_TEMPLATES.glob("*.json")))
    assert payload["failed_count"] >= 1
    assert (output_dir / "batch_index.html").exists()


def test_engineering_workflow_batch_does_not_import_formula_modules():
    source = Path("src/sp63_core/workflows/engineering_workflow_batch.py").read_text(
        encoding="utf-8"
    )

    assert "sp63_core.checks.bending" not in source
    assert "sp63_core.checks.shear" not in source
    assert "sp63_core.checks.cracking" not in source
    assert "sp63_core.checks.crack_width" not in source
    assert "sp63_core.checks.deflection" not in source
