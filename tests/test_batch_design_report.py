import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.report.batch_report import build_batch_design_reports

BATCH_EXAMPLES_DIR = "docs/reports/examples/batch"


def test_batch_design_reports_from_example_directory(tmp_path):
    output_dir = tmp_path / "batch"
    input_paths = sorted(Path(BATCH_EXAMPLES_DIR).glob("*.json"))

    result = build_batch_design_reports(input_paths=input_paths, output_dir=output_dir)

    assert result.requires_engineer_review is True
    assert result.completeness_status == "incomplete"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use_status == "prohibited"
    assert result.project_use is False
    assert result.input_count == 3
    assert result.report_count == 3
    assert result.passed_count == 0
    assert result.failed_count == 0
    assert result.review_count == 3
    assert (output_dir / "index.md").exists()
    assert (output_dir / "index.json").exists()
    assert (output_dir / "manifest.json").exists()
    index = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    assert index["report_type"] == "batch_design_report_index"
    assert index["project_use_status"] == "prohibited"
    assert index["project_use"] is False
    assert {"case_id", "strength_status", "serviceability_status", "overall_status"}.issubset(
        index["cases"][0]
    )
    assert all(case["project_use_status"] == "prohibited" for case in index["cases"])
    assert all(case["project_use"] is False for case in index["cases"])
    assert all(
        case["strength_status"] == "outside_applicability"
        for case in index["cases"]
    )
    for case_id in ("case_001", "case_002", "case_003"):
        case_dir = output_dir / case_id
        assert (case_dir / "report.md").exists()
        assert (case_dir / "report.json").exists()
        assert (case_dir / "report.html").exists()
        assert (case_dir / "input.json").exists()
        assert (case_dir / "manifest.json").exists()


def test_batch_design_reports_invalid_input_does_not_stop_other_cases(tmp_path):
    valid_input = Path(BATCH_EXAMPLES_DIR) / "case_pass_base.json"
    invalid_input = tmp_path / "invalid.json"
    invalid_input.write_text('{"h": 500}', encoding="utf-8")

    result = build_batch_design_reports(
        input_paths=(valid_input, invalid_input),
        output_dir=tmp_path / "batch",
    )

    assert result.input_count == 2
    assert result.report_count == 1
    assert result.status == "review_required"
    assert result.index_json["cases"][1]["overall_status"] == "input_error"
    assert "missing required design report input fields" in result.index_json["cases"][1]["error"]


def test_cli_design_report_batch_text_output(tmp_path, capsys):
    output_dir = tmp_path / "batch_cli"
    exit_code = main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Batch design reports written" in captured.out
    assert (output_dir / "index.md").exists()
    assert (output_dir / "case_001" / "report.md").exists()


def test_cli_design_report_batch_json_output(tmp_path, capsys):
    output_dir = tmp_path / "batch_cli_json"
    exit_code = main(
        [
            "design-report-batch",
            "--input-dir",
            BATCH_EXAMPLES_DIR,
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "design-report-batch"
    assert payload["index"]["report_type"] == "batch_design_report_index"
    assert "manifest_path" in payload["index"]
    assert payload["index"]["input_count"] == 3
    assert payload["index"]["report_count"] == 3
    assert payload["project_use_status"] == "prohibited"
    assert payload["project_use"] is False
    assert payload["index"]["project_use_status"] == "prohibited"
    assert payload["index"]["project_use"] is False
    assert payload["index"]["cases"][0]["requires_engineer_review"] is True
    assert "manifest_path" in payload["index"]["cases"][0]
    assert "report_json_sha256" in payload["index"]["cases"][0]


def test_cli_design_report_batch_repeated_input_json(tmp_path, capsys):
    output_dir = tmp_path / "batch_cli_list"
    exit_code = main(
        [
            "design-report-batch",
            "--input-json",
            f"{BATCH_EXAMPLES_DIR}/case_pass_base.json",
            "--input-json",
            f"{BATCH_EXAMPLES_DIR}/case_serviceability_review.json",
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["input_count"] == 2
    assert payload["report_count"] == 2
    assert (output_dir / "case_002" / "input.json").exists()
