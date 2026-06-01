import json

from sp63_core.cli import main
from sp63_core.ml import run_synthetic_ml_benchmark

SMOKE_GOAL = {"pass": 2, "fail": 2, "review_or_fail": 2}


def test_synthetic_ml_benchmark_runs_pipeline_and_writes_reports(tmp_path):
    output_dir = tmp_path / "synthetic_ml_benchmark"

    result = run_synthetic_ml_benchmark(
        output_dir=output_dir,
        target_distribution_goal=SMOKE_GOAL,
        seed=42,
        max_attempts=1000,
    )

    payload = json.loads((output_dir / "benchmark_report.json").read_text(encoding="utf-8"))
    rows = (output_dir / "dataset" / "synthetic_dataset.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()

    assert result.benchmark_status == "review_required"
    assert result.final_distribution == SMOKE_GOAL
    assert result.accepted_count == 6
    assert result.report_count == 6
    assert result.dataset_row_count == 6
    assert result.synthetic_data_only is True
    assert result.requires_engineer_review is True
    assert result.ml_is_advisory_only is True
    assert result.deterministic_checks_required is True
    assert result.balance_status in {"pass", "review_required"}
    assert result.quality_status in {"pass", "review_required"}
    assert result.feature_status in {"pass", "review_required"}
    assert result.baseline_status in {"pass", "review_required"}
    assert result.neural_status in {"pass", "review_required"}
    assert "metrics" in result.baseline_metrics
    assert "metrics" in result.neural_metrics
    assert payload["report_type"] == "synthetic_ml_benchmark"
    assert payload["target_distribution_goal"] == SMOKE_GOAL
    assert len(rows) == 6
    assert (output_dir / "benchmark_report.md").exists()
    assert (output_dir / "README_BENCHMARK.md").exists()
    assert any("not production evidence" in warning for warning in result.warnings)


def test_synthetic_ml_benchmark_deterministic_derived_features_warn(tmp_path):
    output_dir = tmp_path / "synthetic_ml_benchmark_derived"

    result = run_synthetic_ml_benchmark(
        output_dir=output_dir,
        target_distribution_goal=SMOKE_GOAL,
        seed=42,
        max_attempts=1000,
        feature_mode="deterministic_derived",
    )

    assert result.final_distribution == SMOKE_GOAL
    assert any(
        "deterministic-derived features may leak design decisions" in warning
        for warning in result.warnings
    )


def test_synthetic_ml_benchmark_no_reports_mode_writes_metadata(tmp_path):
    output_dir = tmp_path / "synthetic_ml_benchmark_no_reports"

    result = run_synthetic_ml_benchmark(
        output_dir=output_dir,
        target_distribution_goal={"pass": 1, "fail": 1, "review_or_fail": 1},
        seed=42,
        max_attempts=500,
        create_reports=False,
    )

    assert result.status == "review_required"
    assert result.report_count == 0
    assert result.dataset_row_count == 0
    assert (output_dir / "benchmark_report.json").exists()
    assert (output_dir / "README_BENCHMARK.md").exists()
    assert any("skipped by --no-reports" in warning for warning in result.warnings)


def test_cli_synthetic_ml_benchmark_json_output(tmp_path, capsys):
    output_dir = tmp_path / "synthetic_ml_benchmark_cli"

    exit_code = main(
        [
            "synthetic-ml-benchmark",
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
            "1000",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "synthetic-ml-benchmark"
    assert payload["status"] == "review_required"
    assert payload["target_distribution_goal"] == SMOKE_GOAL
    assert payload["final_distribution"] == SMOKE_GOAL
    assert payload["dataset_row_count"] == 6
    assert payload["synthetic_data_only"] is True
    assert payload["ml_is_advisory_only"] is True


def test_cli_synthetic_ml_benchmark_markdown_output(tmp_path, capsys):
    output_dir = tmp_path / "synthetic_ml_benchmark_markdown"

    exit_code = main(
        [
            "synthetic-ml-benchmark",
            "--output-dir",
            str(output_dir),
            "--target-pass",
            "1",
            "--target-fail",
            "1",
            "--target-review",
            "1",
            "--seed",
            "42",
            "--max-attempts",
            "500",
            "--no-reports",
            "--markdown",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Synthetic ML Benchmark - Advisory Only" in captured.out
    assert "ML remains advisory-only" in captured.out
