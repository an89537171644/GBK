import json
from pathlib import Path

from sp63_core.cli import main
from sp63_core.dataset import (
    analyze_synthetic_dataset_balance,
    export_dataset_from_report_archive,
    generate_guided_synthetic_inputs,
)
from sp63_core.design import design_rectangular_element
from sp63_core.report import (
    load_rectangular_design_input_from_json,
    rectangular_design_input_from_mapping,
)

SMOKE_GOAL = {"pass": 2, "fail": 2, "review_or_fail": 2}


def test_guided_generator_creates_balanced_cases_and_manifest(tmp_path):
    output_dir = tmp_path / "guided_inputs"

    result = generate_guided_synthetic_inputs(
        output_dir=output_dir,
        target_distribution_goal=SMOKE_GOAL,
        seed=42,
        max_attempts=500,
    )
    manifest = json.loads((output_dir / "guided_synthetic_manifest.json").read_text())

    assert result.status == "pass"
    assert result.accepted_count == 6
    assert result.final_distribution == SMOKE_GOAL
    assert result.completeness_status == "incomplete"
    assert result.evidence_status == "needs_engineer_review"
    assert result.project_use_status == "prohibited"
    assert result.project_use is False
    assert len(sorted(output_dir.glob("case_*.json"))) == 6
    assert (output_dir / "README_GUIDED_SYNTHETIC.md").exists()
    assert manifest["generator"] == "guided_synthetic_inputs"
    assert manifest["target_distribution_goal"] == SMOKE_GOAL
    assert manifest["final_distribution"] == SMOKE_GOAL
    assert manifest["synthetic_data_only"] is True
    assert manifest["completeness_status"] == "incomplete"
    assert manifest["evidence_status"] == "needs_engineer_review"
    assert manifest["project_use_status"] == "prohibited"
    assert manifest["project_use"] is False
    assert manifest["requires_engineer_review"] is True
    assert manifest["ml_is_advisory_only"] is True
    assert manifest["deterministic_checks_required"] is True
    assert all(case["sha256"] for case in manifest["cases"])
    readme = (output_dir / "README_GUIDED_SYNTHETIC.md").read_text(encoding="utf-8")
    assert "completeness_status: `incomplete`" in readme
    assert "evidence_status: `needs_engineer_review`" in readme
    assert "project_use_status: `prohibited`" in readme
    assert "project_use: `false`" in readme


def test_guided_cases_load_with_existing_reader_and_record_deterministic_status(tmp_path):
    output_dir = tmp_path / "guided_inputs"
    generate_guided_synthetic_inputs(
        output_dir=output_dir,
        target_distribution_goal=SMOKE_GOAL,
        seed=42,
        max_attempts=500,
    )
    manifest = json.loads((output_dir / "guided_synthetic_manifest.json").read_text())

    for case in manifest["cases"]:
        input_path = output_dir / case["path"]
        design_input = load_rectangular_design_input_from_json(input_path)
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        result = design_rectangular_element(rectangular_design_input_from_mapping(payload))
        assert design_input.b > 0
        assert design_input.h > 0
        assert design_input.load_duration == "short"
        assert case["overall_status"] == result.overall_status


def test_guided_generator_review_goal_without_serviceability_requires_review(tmp_path):
    output_dir = tmp_path / "guided_no_serviceability"

    result = generate_guided_synthetic_inputs(
        output_dir=output_dir,
        target_distribution_goal={"pass": 1, "fail": 1, "review_or_fail": 1},
        seed=42,
        max_attempts=20,
        include_serviceability=False,
    )

    assert result.status == "review_required"
    assert result.final_distribution.get("review_or_fail", 0) == 0
    assert "target distribution goal was not fully reached" in result.warnings
    assert any("serviceability" in warning for warning in result.warnings)


def test_cli_guided_synthetic_inputs_json(tmp_path, capsys):
    output_dir = tmp_path / "guided_inputs"

    exit_code = main(
        [
            "guided-synthetic-inputs",
            "--output-dir",
            str(output_dir),
            "--target-pass",
            "2",
            "--target-fail",
            "2",
            "--target-review",
            "2",
            "--seed",
            "42",
            "--max-attempts",
            "500",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "guided-synthetic-inputs"
    assert payload["status"] == "pass"
    assert payload["accepted_count"] == 6
    assert payload["final_distribution"] == SMOKE_GOAL
    assert payload["completeness_status"] == "incomplete"
    assert payload["evidence_status"] == "needs_engineer_review"
    assert payload["project_use_status"] == "prohibited"
    assert payload["project_use"] is False


def test_cli_guided_synthetic_inputs_text_has_hard_safety_fields(tmp_path, capsys):
    exit_code = main(
        [
            "guided-synthetic-inputs",
            "--output-dir",
            str(tmp_path / "guided_inputs"),
            "--target-pass",
            "1",
            "--target-fail",
            "0",
            "--target-review",
            "0",
            "--seed",
            "42",
            "--max-attempts",
            "100",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "completeness_status: incomplete" in captured.out
    assert "evidence_status: needs_engineer_review" in captured.out
    assert "project_use_status: prohibited" in captured.out
    assert "project_use: false" in captured.out


def test_guided_inputs_feed_batch_export_and_balance_gate(tmp_path, capsys):
    pipeline_goal = {"pass": 3, "fail": 3, "review_or_fail": 3}
    input_dir = tmp_path / "guided_inputs"
    reports_dir = tmp_path / "guided_reports"
    dataset_path = tmp_path / "guided_dataset.jsonl"
    generate_guided_synthetic_inputs(
        output_dir=input_dir,
        target_distribution_goal=pipeline_goal,
        seed=42,
        max_attempts=500,
    )

    exit_code = main(
        [
            "design-report-batch",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(reports_dir),
            "--json",
        ]
    )
    captured = capsys.readouterr()
    batch_payload = json.loads(captured.out)
    assert exit_code == 0
    assert batch_payload["input_count"] == 9
    assert batch_payload["report_count"] == 9

    export_result = export_dataset_from_report_archive(
        source_path=reports_dir,
        output_path=dataset_path,
        output_format="jsonl",
    )
    balance = analyze_synthetic_dataset_balance(
        dataset_path=dataset_path,
        min_rows=9,
        min_class_count=3,
    )

    assert export_result.status == "pass"
    assert export_result.row_count == 9
    assert balance.target_distribution == pipeline_goal
    assert balance.required_classes_present is True
    assert balance.stratified_split_ready is True


def test_committed_guided_manifest_is_not_required():
    example_dir = Path("docs/reports/examples/synthetic_batch_smoke")

    assert not (example_dir / "guided_synthetic_manifest.json").exists()
